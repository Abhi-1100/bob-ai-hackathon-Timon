import React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { User, Mail, ArrowRight } from 'lucide-react';
import { AuthLayout } from '../components/auth/AuthLayout';
import { AuthCard } from '../components/auth/AuthCard';
import { AuthHeader } from '../components/auth/AuthHeader';
import { AuthInput } from '../components/auth/AuthInput';
import { PasswordInput } from '../components/auth/PasswordInput';
import { AuthButton } from '../components/auth/AuthButton';
import { AuthDivider } from '../components/auth/AuthDivider';
import { AuthFooter } from '../components/auth/AuthFooter';
import { useAuthStore } from '../store/authStore';
import { useToast } from '../components/auth/Toast';

const registerSchema = z
  .object({
    name: z.string().min(2, 'Full name is required (min 2 characters)'),
    email: z.string().min(1, 'Email is required').email('Enter a valid email address'),
    password: z.string().min(8, 'Password must contain at least 8 characters'),
    confirmPassword: z.string().min(1, 'Please confirm your password'),
    acceptTerms: z.boolean().refine((val) => val === true, {
      message: 'You must agree to the terms to continue',
    }),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: 'Passwords do not match',
    path: ['confirmPassword'],
  });

export function RegisterPage({ navigate, theme, toggleTheme }) {
  const { register: registerUser, loading, authError, clearError } = useAuthStore();
  const { showToast } = useToast();

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      name: '',
      email: '',
      password: '',
      confirmPassword: '',
      acceptTerms: true,
    },
  });

  const passwordVal = watch('password');
  const confirmPasswordVal = watch('confirmPassword');

  const onSubmit = async (data) => {
    clearError();
    const res = await registerUser(data);
    if (res.success) {
      try {
        localStorage.setItem('d2_has_uploaded', 'false');
      } catch {}
      showToast('Account created! Please upload your alert CSV to initialize the platform.', 'success');
      setTimeout(() => {
        if (navigate) navigate('/upload');
      }, 600);
    } else {
      showToast(res.error, 'error');
    }
  };

  return (
    <AuthLayout navigate={navigate} theme={theme} toggleTheme={toggleTheme}>
      <AuthCard>
        <AuthHeader
          title="Create your account"
          subtitle="Get started with smart threat intelligence in under a minute."
          badge="Get Started"
        />

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

        <form onSubmit={handleSubmit(onSubmit)} style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {/* Full Name - Full Width */}
          <AuthInput
            label="Full Name"
            icon={User}
            placeholder="Alex Vance"
            error={errors.name?.message}
            {...register('name')}
          />

          {/* Work Email - Full Width */}
          <AuthInput
            label="Work Email"
            type="email"
            icon={Mail}
            placeholder="alex@company.com"
            error={errors.email?.message}
            {...register('email')}
          />

          {/* Password - Full Width */}
          <PasswordInput
            label="Password"
            value={passwordVal}
            error={errors.password?.message}
            placeholder="At least 8 characters"
            {...register('password')}
          />

          {/* Confirm Password - Full Width */}
          <PasswordInput
            label="Confirm Password"
            value={confirmPasswordVal}
            error={errors.confirmPassword?.message}
            placeholder="Re-enter your password"
            {...register('confirmPassword')}
          />

          <div style={{ display: 'flex', flexDirection: 'column', gap: 2, marginTop: 2 }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: 7, color: 'var(--text-secondary)', fontSize: 12, cursor: 'pointer' }}>
              <input
                type="checkbox"
                style={{ accentColor: 'var(--blue)' }}
                {...register('acceptTerms')}
              />
              <span>I agree to the Terms of Service and Privacy Policy.</span>
            </label>
            {errors.acceptTerms && (
              <span style={{ fontSize: 11, color: '#EF4444', fontWeight: 500 }}>
                {errors.acceptTerms.message}
              </span>
            )}
          </div>

          <AuthButton type="submit" loading={loading} icon={ArrowRight}>
            Create Account
          </AuthButton>
        </form>

        <AuthFooter mode="register" navigate={navigate} />
      </AuthCard>
    </AuthLayout>
  );
}

export default RegisterPage;
