import {
  Controller,
  Post,
  UseInterceptors,
  UploadedFile,
  BadRequestException,
  Get,
} from '@nestjs/common';
import { FileInterceptor } from '@nestjs/platform-express';
import { ApiTags, ApiOperation, ApiConsumes, ApiBody } from '@nestjs/swagger';
import { ExcelService } from './excel.service';

@ApiTags('excel')
@Controller('api/excel')
export class ExcelController {
  constructor(private readonly excelService: ExcelService) {}

  @Post('upload')
  @ApiOperation({ summary: 'Subir archivo Excel de empleados' })
  @ApiConsumes('multipart/form-data')
  @ApiBody({
    schema: {
      type: 'object',
      properties: {
        file: {
          type: 'string',
          format: 'binary',
          description: 'Archivo Excel (.xlsx, .xlsm)',
        },
      },
    },
  })
  @UseInterceptors(FileInterceptor('file'))
  async uploadFile(@UploadedFile() file: Express.Multer.File) {
    if (!file) {
      throw new BadRequestException('No se proporcionó ningún archivo');
    }

    const validExtensions = ['.xlsx', '.xlsm'];
    const ext = file.originalname.toLowerCase().slice(-5);
    if (!validExtensions.some((ve) => ext.endsWith(ve))) {
      throw new BadRequestException('Formato de archivo no válido. Use .xlsx o .xlsm');
    }

    const success = await this.excelService.loadFromBuffer(file.buffer);

    if (!success) {
      throw new BadRequestException('Error al procesar el archivo Excel');
    }

    const stats = await this.excelService.getSummaryStats();

    return {
      success: true,
      message: 'Archivo cargado correctamente',
      filename: file.originalname,
      stats,
    };
  }

  @Get('status')
  @ApiOperation({ summary: 'Verificar si hay datos cargados' })
  async getStatus() {
    return {
      loaded: this.excelService.isDataLoaded(),
      employeeCount: this.excelService.getAllEmployees().length,
    };
  }
}
