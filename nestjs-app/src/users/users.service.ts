import { Injectable, OnModuleInit } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import * as bcrypt from 'bcrypt';
import { User } from '../database/entities/user.entity';

@Injectable()
export class UsersService implements OnModuleInit {
  constructor(
    @InjectRepository(User)
    private usersRepository: Repository<User>,
  ) {}

  async onModuleInit() {
    // Create default admin user if not exists
    await this.createDefaultAdmin();
  }

  private async createDefaultAdmin() {
    const existingAdmin = await this.findByUsername('Jpkken');
    if (!existingAdmin) {
      const hashedPassword = await bcrypt.hash('57UD10R@', 10);
      const admin = this.usersRepository.create({
        username: 'Jpkken',
        password: hashedPassword,
        role: 'admin',
        email: 'admin@uns.co.jp',
        isActive: true,
      });
      await this.usersRepository.save(admin);
      console.log('✅ Admin user created: Jpkken');
    }
  }

  async findByUsername(username: string): Promise<User | null> {
    return this.usersRepository.findOne({ where: { username } });
  }

  async findById(id: number): Promise<User | null> {
    return this.usersRepository.findOne({ where: { id } });
  }

  async validatePassword(user: User, password: string): Promise<boolean> {
    return bcrypt.compare(password, user.password);
  }

  async updateLastLogin(userId: number): Promise<void> {
    await this.usersRepository.update(userId, { lastLogin: new Date() });
  }

  async createUser(
    username: string,
    password: string,
    role: string = 'viewer',
    email?: string,
  ): Promise<User> {
    const hashedPassword = await bcrypt.hash(password, 10);
    const user = this.usersRepository.create({
      username,
      password: hashedPassword,
      role,
      email,
      isActive: true,
    });
    return this.usersRepository.save(user);
  }

  async getAllUsers(): Promise<Omit<User, 'password'>[]> {
    const users = await this.usersRepository.find();
    return users.map(({ password, ...user }) => user);
  }

  async deleteUser(id: number): Promise<void> {
    await this.usersRepository.delete(id);
  }

  async changePassword(userId: number, newPassword: string): Promise<void> {
    const hashedPassword = await bcrypt.hash(newPassword, 10);
    await this.usersRepository.update(userId, { password: hashedPassword });
  }
}
