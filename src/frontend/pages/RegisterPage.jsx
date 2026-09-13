import React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { User, Mail, ArrowRight, Building2 } from 'lucide-react';
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
    email: z.string().min(1, 'Work email is required').email('Enter a valid enterprise email address'),
    organization: z.string().optional(),
    role: z.string().default('SOC Analyst'),
    password: z.string().min(8, 'Password must contain at least 8 characters'),
    confirmPassword: z.string().min(1, 'Please confirm your password'),
    acceptTerms: z.boolean().refine((val) => val === true, {
      message: 'You must accept the security protocols to continue',
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
      name: 'Alex Vance',
      email: 'alex.vance@sentinelforge.mil',
      organization: 'Vance Cyber Defense Lab',
      role: 'Threat Intelligence Analyst',
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
      showToast('Account successfully provisioned! Redirecting to login…', 'success');
      setTimeout(() => {
        if (navigate) navigate('/login');
      }, 700);
    } else {
      showToast(res.error, 'error');
    }
  };

  return (
    <AuthLayout navigate={navigate} theme={theme} toggleTheme={toggleTheme}>
      <AuthCard>
        <AuthHeader
          title="Provision Operator Account"
          subtitle="Provision your SOC organization with AI threat correlation in under 60 seconds."
          badge="Enterprise Tenant Provisioning"
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
          {/* Row 1: Name & Email */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
            <AuthInput
              label="Full Name"
              icon={User}
              placeholder="Alex Vance"
              error={errors.name?.message}
              {...register('name')}
            />

            <AuthInput
              label="Work Email"
              type="email"
              icon={Mail}
              placeholder="alex@company.com"
              error={errors.email?.message}
              {...register('email')}
            />
          </div>

          {/* Row 2: Organization & Role */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
            <AuthInput
              label="Organization / Domain"
              icon={Building2}
              placeholder="Acme Cyber Lab"
              error={errors.organization?.message}
              {...register('organization')}
            />

            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              <label
                style={{
                  fontSize: 12,
                  fontWeight: 700,
                  color: 'var(--text-secondary)',
                  letterSpacing: '0.04em',
                  textTransform: 'uppercase',
                }}
              >
                Operational Role
              </label>
              <select
                style={{
                  width: '100%',
                  background: 'var(--input-bg)',
                  border: '1px solid var(--input-border)',
                  borderRadius: 9,
                  padding: '9px 12px',
                  color: 'var(--input-text)',
                  fontSize: 13,
                  outline: 'none',
                  fontFamily: 'inherit',
                  boxSizing: 'border-box',
                }}
                {...register('role')}
              >
                <option value="Tier 2/3 SOC Analyst">Tier 2/3 SOC Analyst</option>
                <option value="Threat Intelligence Analyst">Threat Intel Analyst</option>
                <option value="Incident Response Lead">Incident Responder</option>
                <option value="CISO / Security Director">CISO / Security Lead</option>
                <option value="Security Operations Manager">SOC Manager</option>
              </select>
            </div>
          </div>

          {/* Row 3: Password & Confirm Password */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
            <PasswordInput
              label="Passphrase"
              value={passwordVal}
              error={errors.password?.message}
              placeholder="Min 8 characters"
              {...register('password')}
            />

            <PasswordInput
              label="Confirm"
              value={confirmPasswordVal}
              error={errors.confirmPassword?.message}
              placeholder="Repeat passphrase"
              {...register('confirmPassword')}
            />
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: 6, color: 'var(--text-secondary)', fontSize: 11.5, cursor: 'pointer' }}>
              <input
                type="checkbox"
                style={{ accentColor: 'var(--blue)' }}
                {...register('acceptTerms')}
              />
              <span>I confirm adherence to Enterprise TLP:AMBER handling protocols.</span>
            </label>
            {errors.acceptTerms && (
              <span style={{ fontSize: 11, color: '#EF4444', fontWeight: 500 }}>
                {errors.acceptTerms.message}
              </span>
            )}
          </div>

          <AuthButton type="submit" loading={loading} icon={ArrowRight}>
            Create Enterprise Account
          </AuthButton>
        </form>

        <AuthFooter mode="register" navigate={navigate} />
      </AuthCard>
    </AuthLayout>
  );
}

export default RegisterPage;
