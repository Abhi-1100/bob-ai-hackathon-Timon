import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { ArrowRight, CheckCircle2, ShieldCheck } from 'lucide-react';
import { AuthLayout } from '../components/auth/AuthLayout';
import { AuthCard } from '../components/auth/AuthCard';
import { AuthHeader } from '../components/auth/AuthHeader';
import { PasswordInput } from '../components/auth/PasswordInput';
import { AuthButton } from '../components/auth/AuthButton';
import { AuthFooter } from '../components/auth/AuthFooter';
import { useAuthStore } from '../store/authStore';
import { useToast } from '../components/auth/Toast';

const resetSchema = z
  .object({
    newPassword: z.string().min(8, 'Passphrase must contain at least 8 characters'),
    confirmPassword: z.string().min(1, 'Please confirm your new password'),
  })
  .refine((data) => data.newPassword === data.confirmPassword, {
    message: 'Passwords do not match',
    path: ['confirmPassword'],
  });

export function ResetPasswordPage({ navigate, theme, toggleTheme }) {
  const { resetPassword, loading, authError, clearError } = useAuthStore();
  const { showToast } = useToast();
  const [token, setToken] = useState('');
  const [isSuccess, setIsSuccess] = useState(false);

  useEffect(() => {
    // Extract token from URL search query (?token=...)
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search);
      const t = params.get('token') || 'demo-reset-token-2026';
      setToken(t);
    }
  }, []);

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(resetSchema),
    defaultValues: {
      newPassword: '',
      confirmPassword: '',
    },
  });

  const passwordVal = watch('newPassword');
  const confirmVal = watch('confirmPassword');

  const onSubmit = async (data) => {
    clearError();
    const res = await resetPassword({ token, newPassword: data.newPassword });
    if (res.success) {
      setIsSuccess(true);
      showToast('Credentials successfully updated!', 'success');
      setTimeout(() => {
        if (navigate) navigate('/login');
      }, 1500);
    } else {
      showToast(res.error, 'error');
    }
  };

  return (
    <AuthLayout navigate={navigate} theme={theme} toggleTheme={toggleTheme}>
      <AuthCard>
        <AuthHeader
          title="Update Credentials"
          subtitle="Establish a new enterprise-grade passphrase for your station."
          badge="Cryptographic Key Exchange"
        />

        {isSuccess ? (
          <div style={{ textAlign: 'center', padding: '16px 0' }}>
            <div
              style={{
                width: 48,
                height: 48,
                borderRadius: '50%',
                background: 'rgba(16, 185, 129, 0.12)',
                border: '1px solid rgba(16, 185, 129, 0.3)',
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginBottom: 16,
              }}
            >
              <CheckCircle2 size={24} color="#10B981" />
            </div>

            <h3 style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-primary)', margin: '0 0 8px 0' }}>
              Passphrase Updated
            </h3>
            <p style={{ fontSize: 13.5, color: 'var(--text-secondary)', lineHeight: 1.6, margin: '0 0 20px 0' }}>
              Your operator credentials have been renewed. Redirecting you to the authentication gateway…
            </p>

            <AuthButton
              type="button"
              onClick={() => navigate && navigate('/login')}
              icon={ArrowRight}
            >
              Proceed to Sign In
            </AuthButton>
          </div>
        ) : (
          <>
            {authError && (
              <div
                style={{
                  padding: '10px 14px',
                  borderRadius: 8,
                  background: 'rgba(239, 68, 68, 0.1)',
                  border: '1px solid rgba(239, 68, 68, 0.3)',
                  color: '#EF4444',
                  fontSize: 12.5,
                  fontWeight: 500,
                  marginBottom: 16,
                }}
              >
                {authError}
              </div>
            )}

            <form onSubmit={handleSubmit(onSubmit)} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              <PasswordInput
                label="New Station Passphrase"
                showStrengthMeter={true}
                value={passwordVal}
                error={errors.newPassword?.message}
                {...register('newPassword')}
              />

              <PasswordInput
                label="Confirm Passphrase"
                value={confirmVal}
                error={errors.confirmPassword?.message}
                {...register('confirmPassword')}
              />

              <AuthButton type="submit" loading={loading} icon={ShieldCheck}>
                Reset Password
              </AuthButton>
            </form>

            <AuthFooter mode="reset-password" navigate={navigate} />
          </>
        )}
      </AuthCard>
    </AuthLayout>
  );
}

export default ResetPasswordPage;
