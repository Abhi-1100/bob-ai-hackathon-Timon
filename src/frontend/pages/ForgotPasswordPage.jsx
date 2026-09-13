import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Mail, ArrowRight, CheckCircle2, KeyRound } from 'lucide-react';
import { AuthLayout } from '../components/auth/AuthLayout';
import { AuthCard } from '../components/auth/AuthCard';
import { AuthHeader } from '../components/auth/AuthHeader';
import { AuthInput } from '../components/auth/AuthInput';
import { AuthButton } from '../components/auth/AuthButton';
import { AuthFooter } from '../components/auth/AuthFooter';
import { useAuthStore } from '../store/authStore';
import { useToast } from '../components/auth/Toast';

const forgotSchema = z.object({
  email: z.string().min(1, 'Email is required').email('Enter a valid email address'),
});

export function ForgotPasswordPage({ navigate, theme, toggleTheme }) {
  const { forgotPassword, loading, authError, clearError } = useAuthStore();
  const { showToast } = useToast();
  const [successData, setSuccessData] = useState(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(forgotSchema),
    defaultValues: {
      email: 'analyst@sentinelforge.mil',
    },
  });

  const onSubmit = async (data) => {
    clearError();
    const res = await forgotPassword(data.email);
    if (res.success) {
      setSuccessData(res.data);
      showToast('Password reset instructions dispatched!', 'success');
    } else {
      showToast(res.error, 'error');
    }
  };

  return (
    <AuthLayout navigate={navigate} theme={theme} toggleTheme={toggleTheme}>
      <AuthCard>
        <AuthHeader
          title="Reset your password"
          subtitle="Enter your email address and we'll send you a link to reset your password."
          badge="Password Help"
        />

        {successData ? (
          <div style={{ textAlign: 'center', padding: '12px 0' }}>
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
              Check Your Inbox
            </h3>

            <p style={{ fontSize: 13.5, color: 'var(--text-secondary)', lineHeight: 1.6, margin: '0 0 20px 0' }}>
              {successData.message}
            </p>

            {successData.reset_url && (
              <div
                style={{
                  background: 'var(--bg-tertiary)',
                  border: '1px solid var(--card-border)',
                  borderRadius: 10,
                  padding: '12px',
                  marginBottom: 20,
                  textAlign: 'left',
                }}
              >
                <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--blue)', textTransform: 'uppercase', marginBottom: 6 }}>
                  ⚡ Quick Test Reset Link (Evaluation Mode)
                </div>
                <button
                  type="button"
                  onClick={() => navigate && navigate(successData.reset_url)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 6,
                    background: 'none',
                    border: 'none',
                    color: 'var(--blue)',
                    fontSize: 12.5,
                    fontWeight: 600,
                    cursor: 'pointer',
                    padding: 0,
                  }}
                >
                  <KeyRound size={14} />
                  <span>Click here to proceed directly to Password Reset →</span>
                </button>
              </div>
            )}

            <button
              type="button"
              onClick={() => navigate && navigate('/login')}
              style={{
                width: '100%',
                padding: '10px',
                borderRadius: 8,
                background: 'var(--card)',
                border: '1px solid var(--card-border)',
                color: 'var(--text-primary)',
                fontSize: 13,
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              Return to Login
            </button>
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
              <AuthInput
                label="Email Address"
                type="email"
                icon={Mail}
                placeholder="alex@company.com"
                error={errors.email?.message}
                {...register('email')}
              />

              <AuthButton type="submit" loading={loading} icon={ArrowRight}>
                Send Reset Link
              </AuthButton>
            </form>

            <AuthFooter mode="forgot-password" navigate={navigate} />
          </>
        )}
      </AuthCard>
    </AuthLayout>
  );
}

export default ForgotPasswordPage;
