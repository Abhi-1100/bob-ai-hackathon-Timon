import React from 'react';
import { AuthPage } from './AuthPage';

export function SignupPage(props) {
  return <AuthPage initialMode="signup" {...props} />;
}

export default SignupPage;
