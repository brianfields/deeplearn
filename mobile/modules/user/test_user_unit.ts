/**
 * User Module Service Unit Tests
 */

import { UserService } from './service';
import { UserRepo } from './repo';
import type { ApiUser } from './models';

jest.mock('./repo');

describe('UserService', () => {
  let service: UserService;
  let repo: jest.Mocked<UserRepo>;
  const apiUser: ApiUser = {
    id: 1,
    email: 'learner@example.com',
    name: 'Test Learner',
    role: 'learner',
    is_active: true,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-02T00:00:00Z',
  };

  beforeEach(() => {
    repo = new UserRepo() as jest.Mocked<UserRepo>;
    service = new UserService(repo);
    jest.clearAllMocks();
  });

  it('registers user and maps to DTO', async () => {
    repo.register.mockResolvedValue(apiUser);

    const result = await service.register({
      email: 'learner@example.com',
      password: 'supersecret',
      name: 'Test Learner',
    });

    expect(repo.register).toHaveBeenCalledWith({
      email: 'learner@example.com',
      password: 'supersecret',
      name: 'Test Learner',
    });
    expect(result).toMatchObject({
      id: apiUser.id,
      email: apiUser.email,
      name: apiUser.name,
      isActive: true,
      isAdmin: false,
    });
    expect(result.createdAt).toBeInstanceOf(Date);
  });

  it('authenticates user via login', async () => {
    repo.login.mockResolvedValue({ user: apiUser });

    const result = await service.login({
      email: 'learner@example.com',
      password: 'supersecret',
    });

    expect(repo.login).toHaveBeenCalled();
    expect(result.email).toEqual(apiUser.email);
  });

  it('returns null for invalid profile id', async () => {
    const result = await service.getProfile(0);
    expect(result).toBeNull();
    expect(repo.getProfile).not.toHaveBeenCalled();
  });

  it('returns null when profile is not found', async () => {
    const error = Object.assign(new Error('Not found'), { status: 404 });
    repo.getProfile.mockRejectedValue(error);

    const result = await service.getProfile(42);

    expect(repo.getProfile).toHaveBeenCalledWith(42);
    expect(result).toBeNull();
  });

  it('validates password when updating profile', async () => {
    await expect(
      service.updateProfile(1, { password: 'short' })
    ).rejects.toMatchObject({
      message: 'Password must be at least 8 characters long',
    });
    expect(repo.updateProfile).not.toHaveBeenCalled();
  });

  it('updates profile with valid payload', async () => {
    const updatedUser: ApiUser = { ...apiUser, name: 'Updated Name' };
    repo.updateProfile.mockResolvedValue(updatedUser);

    const result = await service.updateProfile(1, { name: 'Updated Name' });

    expect(repo.updateProfile).toHaveBeenCalledWith(1, {
      name: 'Updated Name',
    });
    expect(result.name).toEqual('Updated Name');
  });
});
