import { Module } from '@nestjs/common';
import { VisasController } from './visas.controller';
import { VisasService } from './visas.service';

@Module({
  controllers: [VisasController],
  providers: [VisasService],
  exports: [VisasService],
})
export class VisasModule {}
