import React from 'react';
import { AuthPage } from './AuthPage';

export function LoginPage(props) {
  return <AuthPage initialMode="login" {...props} />;
}

export default LoginPage;
