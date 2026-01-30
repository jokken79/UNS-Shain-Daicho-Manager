import { NestFactory } from '@nestjs/core';
import { NestExpressApplication } from '@nestjs/platform-express';
import { SwaggerModule, DocumentBuilder } from '@nestjs/swagger';
import { ValidationPipe } from '@nestjs/common';
import { join } from 'path';
import { AppModule } from './app.module';

async function bootstrap() {
  const app = await NestFactory.create<NestExpressApplication>(AppModule);

  // Enable validation
  app.useGlobalPipes(
    new ValidationPipe({
      whitelist: true,
      transform: true,
      forbidNonWhitelisted: true,
    }),
  );

  // Enable CORS
  app.enableCors();

  // Set up views (Handlebars)
  app.setBaseViewsDir(join(__dirname, '..', 'views'));
  app.setViewEngine('hbs');

  // Serve static files
  app.useStaticAssets(join(__dirname, '..', 'public'));

  // Swagger API documentation
  const config = new DocumentBuilder()
    .setTitle('UNS Shain Daicho API')
    .setDescription('API para gestión de registro de empleados - Universal Kikaku')
    .setVersion('2.0.0')
    .addTag('employees', 'Gestión de empleados')
    .addTag('visas', 'Alertas de visa')
    .addTag('salaries', 'Análisis de salarios')
    .addTag('reports', 'Reportes y exportación')
    .build();

  const document = SwaggerModule.createDocument(app, config);
  SwaggerModule.setup('api/docs', app, document);

  const port = process.env.PORT || 3000;
  await app.listen(port);

  console.log(`
╔══════════════════════════════════════════════════════════════╗
║     UNS Shain Daicho Manager - NestJS API                    ║
║══════════════════════════════════════════════════════════════║
║  Web UI:      http://localhost:${port}                          ║
║  API Docs:    http://localhost:${port}/api/docs                 ║
║  Health:      http://localhost:${port}/api/health               ║
╚══════════════════════════════════════════════════════════════╝
  `);
}

bootstrap();
