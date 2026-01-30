import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  UpdateDateColumn,
  Index,
} from 'typeorm';

@Entity('employees')
@Index(['nationality'])
@Index(['category'])
@Index(['currentStatus'])
export class Employee {
  @PrimaryGeneratedColumn()
  id: number;

  @Column({ unique: true })
  employeeId: number;

  @Column({ length: 100 })
  name: string;

  @Column({ length: 100, nullable: true })
  nameKana: string;

  @Column({ length: 20, default: '在職中' })
  currentStatus: string;

  @Column({ length: 50, nullable: true })
  nationality: string;

  @Column({ type: 'date', nullable: true })
  hireDate: Date;

  @Column({ type: 'date', nullable: true })
  resignationDate: Date;

  @Column({ type: 'date', nullable: true })
  visaExpiry: Date;

  @Column({ length: 50, nullable: true })
  visaType: string;

  @Column({ type: 'decimal', precision: 10, scale: 2, nullable: true })
  hourlyRate: number;

  @Column({ type: 'decimal', precision: 10, scale: 2, nullable: true })
  billingRate: number;

  @Column({ type: 'decimal', precision: 10, scale: 2, nullable: true })
  profitMargin: number;

  @Column({ length: 100, nullable: true })
  dispatchCompany: string;

  @Column({ nullable: true })
  age: number;

  @Column({ length: 30 })
  category: string;

  @CreateDateColumn()
  createdAt: Date;

  @UpdateDateColumn()
  updatedAt: Date;
}
