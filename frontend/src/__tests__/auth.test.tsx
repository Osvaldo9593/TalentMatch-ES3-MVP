import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '../context/AuthContext';
import { LoginPage } from '../pages/LoginPage';
import { vi, describe, it, expect, beforeEach } from 'vitest';

describe('autenticación', () => {
  beforeEach(() => {
    sessionStorage.clear();
    vi.restoreAllMocks();
  });

  it('renderiza el login y muestra credenciales inválidas', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      json: async () => ({ detail: 'Correo o contraseña incorrectos' }),
    } as Response);
    render(<BrowserRouter><AuthProvider><LoginPage /></AuthProvider></BrowserRouter>);
    fireEvent.change(screen.getByLabelText('Correo'), { target: { value: 'user@test.local' } });
    fireEvent.change(screen.getByLabelText('Contraseña'), { target: { value: 'bad-password' } });
    fireEvent.click(screen.getByRole('button', { name: 'Ingresar' }));
    expect((await screen.findByRole('alert')).textContent).toContain('Correo o contraseña incorrectos');
  });

  it('guarda el token después de autenticar', async () => {
    global.fetch = vi.fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ access_token: 'test-token', token_type: 'bearer' }),
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          id: 1,
          email: 'user@test.local',
          role: 'recruiter',
          is_active: true,
          created_at: '2026-01-01T00:00:00Z',
        }),
      } as Response);
    render(<BrowserRouter><AuthProvider><LoginPage /></AuthProvider></BrowserRouter>);
    fireEvent.change(screen.getByLabelText('Correo'), { target: { value: 'user@test.local' } });
    fireEvent.change(screen.getByLabelText('Contraseña'), { target: { value: 'password' } });
    fireEvent.click(screen.getByRole('button', { name: 'Ingresar' }));
    await waitFor(() => expect(sessionStorage.getItem('talentmatch_access_token')).toBe('test-token'));
  });
});
