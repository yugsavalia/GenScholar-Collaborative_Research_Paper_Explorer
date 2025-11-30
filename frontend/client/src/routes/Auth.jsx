import { useState, useEffect, useRef } from 'react';
import { useLocation } from 'wouter';
import { Formik, Form, Field } from 'formik';
import { useAuth } from '../context/AuthContext';
import { loginSchema, createAccountSchema } from '../utils/validators';
import { requestEmailVerification, verifyEmailToken, verifyOTP } from '../api/auth';
import Input from '../components/Input';
import Button from '../components/Button';
import * as Yup from 'yup';

const emailSchema = Yup.object().shape({
  email: Yup.string().email('Invalid email address').required('Email is required'),
});

export default function Auth() {
  const [location, setLocation] = useLocation();
  const { login, signup, isAuthenticated } = useAuth();
  
  const searchParams = new URLSearchParams(location.split('?')[1]);
  const initialTab = searchParams.get('tab') === 'create' ? 'create' : 'login';
  const [activeTab, setActiveTab] = useState(initialTab);
  const [error, setError] = useState('');
  const [emailVerificationStep, setEmailVerificationStep] = useState('request'); // 'request', 'otp', or 'signup'
  const [verifiedEmail, setVerifiedEmail] = useState(null);
  const [verificationToken, setVerificationToken] = useState(null);
  const [emailSent, setEmailSent] = useState(false);
  const [currentEmail, setCurrentEmail] = useState('');
  const [otpValues, setOtpValues] = useState(['', '', '', '', '', '']);
  const [otpError, setOtpError] = useState('');
  const otpInputRefs = useRef([]);
  
  // Check if we have a verification token in URL (from email link)
  useEffect(() => {
    const token = searchParams.get('token');
    if (token && activeTab === 'create') {
      // User clicked email verification link
      verifyEmailToken(token).then(data => {
        setVerifiedEmail(data.email);
        setVerificationToken(data.token);
        setEmailVerificationStep('signup');
        setError('');
      }).catch(err => {
        setError(err.message || 'Invalid or expired verification link');
      });
    }
  }, [location, activeTab, searchParams]);

  useEffect(() => {
    if (isAuthenticated) {
      setLocation('/dashboard');
    }
  }, [isAuthenticated, setLocation]);

  const handleEmailVerificationRequest = async (values, { setSubmitting }) => {
    try {
      setError('');
      setEmailSent(false);
      setOtpError('');
      setOtpValues(['', '', '', '', '', '']);
      await requestEmailVerification(values.email);
      setCurrentEmail(values.email);
      setEmailSent(true);
      setEmailVerificationStep('otp');
      // Focus first OTP input after a short delay
      setTimeout(() => {
        if (otpInputRefs.current[0]) {
          otpInputRefs.current[0].focus();
        }
      }, 100);
    } catch (error) {
      const errorMessage = error.message || error.data?.message || 'Failed to send verification email';
      setError(errorMessage);
      console.error('Email verification error:', error);
    } finally {
      setSubmitting(false);
    }
  };

  const handleOTPChange = (index, value) => {
    // Only allow digits
    if (value && !/^\d$/.test(value)) {
      return;
    }
    
    const newOtpValues = [...otpValues];
    newOtpValues[index] = value;
    setOtpValues(newOtpValues);
    setOtpError('');
    
    // Auto-advance to next input
    if (value && index < 5) {
      otpInputRefs.current[index + 1]?.focus();
    }
  };

  const handleOTPKeyDown = (index, e) => {
    // Handle backspace
    if (e.key === 'Backspace' && !otpValues[index] && index > 0) {
      otpInputRefs.current[index - 1]?.focus();
    }
  };

  const handleOTPPaste = (e) => {
    e.preventDefault();
    const pastedData = e.clipboardData.getData('text').trim();
    if (/^\d{6}$/.test(pastedData)) {
      const newOtpValues = pastedData.split('').slice(0, 6);
      setOtpValues(newOtpValues);
      setOtpError('');
      // Focus last input
      otpInputRefs.current[5]?.focus();
    }
  };

  const handleOTPVerification = async () => {
    const otp = otpValues.join('');
    
    if (otp.length !== 6) {
      setOtpError('Please enter all 6 digits');
      return;
    }
    
    try {
      setOtpError('');
      setError('');
      await verifyOTP(currentEmail, otp);
      setVerifiedEmail(currentEmail);
      setEmailVerificationStep('signup');
    } catch (error) {
      const errorMessage = error.message || error.data?.message || 'Invalid OTP';
      setOtpError(errorMessage);
      setOtpValues(['', '', '', '', '', '']);
      if (otpInputRefs.current[0]) {
        otpInputRefs.current[0].focus();
      }
    }
  };

  const handleSubmit = async (values, { setSubmitting }) => {
    try {
      setError(''); // Clear previous errors
      
      if (activeTab === 'login') {
        // Login - identifier can be username OR email
        await login(values.identifier, values.password);
        setLocation('/dashboard');
      } else {
        // Signup - requires verified email
        if (!verifiedEmail) {
          setError('Email verification required. Please verify your email first.');
          setSubmitting(false);
          return;
        }
        await signup(values.username, verifiedEmail, values.password, values.confirm_password);
        setLocation('/dashboard');
      }
    } catch (error) {
      // Extract error message from backend response
      const errorMessage = error.message || error.data?.message || 'An error occurred. Please try again.';
      setError(errorMessage);
      console.error('Auth error:', error);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4" style={{ background: 'var(--bg-color)' }}>
      <div className="w-full max-w-[400px]">
        <div className="rounded-lg p-8" style={{ background: 'var(--panel-color)', border: '1px solid var(--border-color)' }}>
          <h1 className="text-2xl font-bold mb-6 text-center" style={{ color: 'var(--text-color)' }}>
            GenScholar
          </h1>
          
          <div className="flex mb-6" style={{ borderBottom: '1px solid var(--border-color)' }}>
            <button
              onClick={() => {
                setActiveTab('login');
                setError(''); // Clear error when switching tabs
              }}
              className={`flex-1 pb-3 text-sm font-medium transition-colors ${
                activeTab === 'login'
                  ? 'border-b-2'
                  : ''
              }`}
              style={activeTab === 'login' 
                ? { color: 'var(--accent-color)', borderBottomColor: 'var(--accent-color)' }
                : { color: 'var(--muted-text)' }
              }
              onMouseEnter={(e) => {
                if (activeTab !== 'login') e.target.style.color = 'var(--text-color)';
              }}
              onMouseLeave={(e) => {
                if (activeTab !== 'login') e.target.style.color = 'var(--muted-text)';
              }}
              data-testid="button-tab-login"
            >
              Login
            </button>
            <button
              onClick={() => {
                setActiveTab('create');
                setError(''); // Clear error when switching tabs
                setEmailVerificationStep('request');
                setEmailSent(false);
                setVerifiedEmail(null);
                setVerificationToken(null);
                setCurrentEmail('');
                setOtpValues(['', '', '', '', '', '']);
                setOtpError('');
              }}
              className={`flex-1 pb-3 text-sm font-medium transition-colors ${
                activeTab === 'create'
                  ? 'border-b-2'
                  : ''
              }`}
              style={activeTab === 'create' 
                ? { color: 'var(--accent-color)', borderBottomColor: 'var(--accent-color)' }
                : { color: 'var(--muted-text)' }
              }
              onMouseEnter={(e) => {
                if (activeTab !== 'create') e.target.style.color = 'var(--text-color)';
              }}
              onMouseLeave={(e) => {
                if (activeTab !== 'create') e.target.style.color = 'var(--muted-text)';
              }}
              data-testid="button-tab-create"
            >
              Create Account
            </button>
          </div>

          {error && (
            <div className="mb-4 p-3 bg-red-500/10 border border-red-500/50 rounded-md">
              <p className="text-red-400 text-sm">{error}</p>
            </div>
          )}

          {activeTab === 'login' ? (
            <Formik
              initialValues={{ identifier: '', password: '' }}
              validationSchema={loginSchema}
              onSubmit={handleSubmit}
            >
              {({ errors, touched, isSubmitting }) => (
                <Form>
                  <Field name="identifier">
                    {({ field }) => (
                      <Input
                        {...field}
                        type="text"
                        label="Email or username"
                        placeholder="Enter your email or username"
                        error={touched.identifier && errors.identifier}
                        data-testid="input-identifier"
                      />
                    )}
                  </Field>
                  
                  <Field name="password">
                    {({ field }) => (
                      <Input
                        {...field}
                        type="password"
                        label="Password"
                        placeholder="Enter your password"
                        error={touched.password && errors.password}
                        data-testid="input-password"
                        maxLength={15}
                      />
                    )}
                  </Field>
                  
                  <div className="text-right mb-4">
                    <button
                      type="button"
                      onClick={() => setLocation('/forgot-password')}
                      className="text-sm text-[#4FC3F7] hover:text-[#3BA7D1] transition-colors"
                      data-testid="link-forgot-password"
                    >
                      Forgot password?
                    </button>
                  </div>

                  <Button
                    type="submit"
                    variant="primary"
                    className="w-full"
                    disabled={isSubmitting}
                    data-testid="button-submit-auth"
                  >
                    Login
                  </Button>
                </Form>
              )}
            </Formik>
          ) : activeTab === 'create' && emailVerificationStep === 'request' ? (
            // Step 1: Request email verification
            <>
              <p className="text-[#BDBDBD] text-sm mb-4">
                Enter your email address. We'll send you a verification code to confirm your email before you can create your account.
              </p>
              <Formik
                initialValues={{ email: '' }}
                validationSchema={emailSchema}
                onSubmit={handleEmailVerificationRequest}
              >
                {({ errors, touched, isSubmitting, values }) => (
                  <Form>
                    <Field name="email">
                      {({ field }) => (
                        <Input
                          {...field}
                          type="email"
                          label="Email"
                          placeholder="Enter your email"
                          error={touched.email && errors.email}
                          data-testid="input-email"
                        />
                      )}
                    </Field>
                    <Button
                      type="submit"
                      variant="primary"
                      className="w-full"
                      disabled={isSubmitting || !values.email || errors.email}
                      data-testid="button-send-otp"
                    >
                      {isSubmitting ? 'Sending...' : 'Send OTP'}
                    </Button>
                  </Form>
                )}
              </Formik>
            </>
          ) : activeTab === 'create' && emailVerificationStep === 'otp' ? (
            // Step 1.5: Verify OTP
            <>
              <p className="text-[#BDBDBD] text-sm mb-4">
                Enter the 6-digit verification code sent to <strong className="text-[#E0E0E0]">{currentEmail}</strong>
              </p>
              
              {otpError && (
                <div className="mb-4 p-3 bg-red-500/10 border border-red-500/50 rounded-md">
                  <p className="text-red-400 text-sm">{otpError}</p>
                </div>
              )}
              
              <div className="flex gap-2 mb-4 justify-center">
                {otpValues.map((value, index) => (
                  <input
                    key={index}
                    ref={(el) => (otpInputRefs.current[index] = el)}
                    type="text"
                    inputMode="numeric"
                    maxLength={1}
                    value={value}
                    onChange={(e) => handleOTPChange(index, e.target.value)}
                    onKeyDown={(e) => handleOTPKeyDown(index, e)}
                    onPaste={handleOTPPaste}
                    className="w-12 h-12 text-center text-lg font-semibold bg-[#2A2A2A] border border-[#3A3A3A] rounded-md text-[#E0E0E0] focus:outline-none focus:border-[#4FC3F7] focus:ring-1 focus:ring-[#4FC3F7]"
                    data-testid={`otp-input-${index}`}
                  />
                ))}
              </div>
              
              <Button
                type="button"
                variant="primary"
                className="w-full mb-3"
                disabled={otpValues.join('').length !== 6}
                onClick={handleOTPVerification}
                data-testid="button-verify-otp"
              >
                Verify OTP
              </Button>
              
              <button
                type="button"
                onClick={() => {
                  setEmailVerificationStep('request');
                  setEmailSent(false);
                  setOtpValues(['', '', '', '', '', '']);
                  setOtpError('');
                }}
                className="w-full text-sm text-[#4FC3F7] hover:text-[#3BA7D1] transition-colors"
                data-testid="button-change-email"
              >
                Change email
              </button>
            </>
          ) : (
            // Step 2: Complete signup after email verification
            <Formik
              initialValues={{ username: '', email: verifiedEmail || '', password: '', confirm_password: '' }}
              validationSchema={createAccountSchema}
              onSubmit={handleSubmit}
              enableReinitialize={true}
            >
              {({ errors, touched, isSubmitting }) => (
                <Form>
                  {verifiedEmail && (
                    <div className="mb-4 p-3 bg-green-500/10 border border-green-500/50 rounded-md">
                      <p className="text-green-400 text-sm">
                        ✓ Email verified: {verifiedEmail}
                      </p>
                    </div>
                  )}
                  
                  <Field name="username">
                    {({ field }) => (
                      <Input
                        {...field}
                        type="text"
                        label="Username"
                        placeholder="Enter your username"
                        error={touched.username && errors.username}
                        data-testid="input-username"
                        maxLength={15}
                      />
                    )}
                  </Field>
                  
                  <Field name="email">
                    {({ field }) => (
                      <Input
                        {...field}
                        type="email"
                        label="Email"
                        value={verifiedEmail || ''}
                        disabled
                        className="bg-[#2A2A2A] opacity-50 cursor-not-allowed"
                        data-testid="input-email-verified"
                      />
                    )}
                  </Field>
                  
                  <Field name="password">
                    {({ field }) => (
                      <Input
                        {...field}
                        type="password"
                        label="Password"
                        placeholder="Enter your password"
                        error={touched.password && errors.password}
                        data-testid="input-password"
                        maxLength={15}
                      />
                    )}
                  </Field>
                  
                  <Field name="confirm_password">
                    {({ field }) => (
                      <Input
                        {...field}
                        type="password"
                        label="Confirm Password"
                        placeholder="Confirm your password"
                        error={touched.confirm_password && errors.confirm_password}
                        data-testid="input-confirm-password"
                      />
                    )}
                  </Field>

                  <Button
                    type="submit"
                    variant="primary"
                    className="w-full"
                    disabled={isSubmitting || !verifiedEmail}
                    data-testid="button-submit-auth"
                  >
                    {isSubmitting ? 'Creating Account...' : 'Create Account'}
                  </Button>
                </Form>
              )}
            </Formik>
          )}
        </div>
      </div>
    </div>
  );
}
