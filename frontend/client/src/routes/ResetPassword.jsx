import { useState, useEffect } from 'react';
import { useLocation, useRoute } from 'wouter';
import { Formik, Form, Field } from 'formik';
import * as Yup from 'yup';
import { confirmPasswordReset } from '../api/passwordReset';
import Input from '../components/Input';
import Button from '../components/Button';

const resetPasswordSchema = Yup.object().shape({
  new_password: Yup.string()
    .min(8, 'Password must be at least 8 characters')
    .required('Password is required'),
  re_new_password: Yup.string()
    .oneOf([Yup.ref('new_password')], 'Passwords must match')
    .required('Please confirm your password'),
});

export default function ResetPassword() {
  const [, params] = useRoute('/reset-password/:uid/:token');
  const [, setLocation] = useLocation();
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [validationErrors, setValidationErrors] = useState({});

  const uid = params?.uid;
  const token = params?.token;

  useEffect(() => {
    if (!uid || !token) {
      setError('Invalid reset link. Please request a new password reset.');
    }
  }, [uid, token]);

  const handleSubmit = async (values) => {
    if (!uid || !token) {
      setError('Invalid reset link. Please request a new password reset.');
      return;
    }

    try {
      setError('');
      setValidationErrors({});
      setIsSubmitting(true);
      
      await confirmPasswordReset(uid, token, values.new_password, values.re_new_password);
      setSuccess(true);
    } catch (err) {
      console.error('Password reset confirmation error:', err);
      
      // Check if it's a validation error with field-specific messages
      if (err.data?.errors) {
        setValidationErrors(err.data.errors);
        setError('Please fix the errors below.');
      } else {
        const errorMessage = err.message || err.data?.message || 'An error occurred. Please try again.';
        if (errorMessage.includes('Invalid') || errorMessage.includes('expired')) {
          setError('Invalid or expired reset link. Please request a new password reset.');
        } else {
          setError(errorMessage);
        }
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  if (success) {
    return (
      <div className="min-h-screen bg-[#121212] flex items-center justify-center px-4">
        <div className="w-full max-w-[400px]">
          <div className="bg-[#1E1E1E] border border-[#2A2A2A] rounded-lg p-8">
            <div className="mb-4 p-3 bg-green-500/10 border border-green-500/50 rounded-md">
              <p className="text-green-400 text-sm">
                Your password has been reset successfully. You can now log in with your new password.
              </p>
            </div>
            
            <Button
              onClick={() => setLocation('/auth')}
              variant="primary"
              className="w-full"
              data-testid="button-go-to-login"
            >
              Go to Login
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#121212] flex items-center justify-center px-4">
      <div className="w-full max-w-[400px]">
        <div className="bg-[#1E1E1E] border border-[#2A2A2A] rounded-lg p-8">
          <h1 className="text-2xl font-bold text-[#E0E0E0] mb-2 text-center">
            Reset your GenScholar password
          </h1>
          <p className="text-[#BDBDBD] text-sm mb-6 text-center">
            Enter your new password below.
          </p>
          
          <Formik
            initialValues={{ new_password: '', re_new_password: '' }}
            validationSchema={resetPasswordSchema}
            onSubmit={handleSubmit}
          >
            {({ errors, touched }) => {
              // Merge Formik errors with API validation errors
              const newPasswordError = validationErrors.new_password?.[0] || (touched.new_password && errors.new_password);
              const reNewPasswordError = validationErrors.re_new_password || (touched.re_new_password && errors.re_new_password);
              
              return (
                <Form>
                  {error && (
                    <div className="mb-4 p-3 bg-red-500/10 border border-red-500/50 rounded-md">
                      <p className="text-red-400 text-sm">{error}</p>
                    </div>
                  )}
                  
                  <Field name="new_password">
                    {({ field }) => (
                      <Input
                        {...field}
                        type="password"
                        label="New password"
                        placeholder="Enter your new password"
                        error={newPasswordError}
                        data-testid="input-new-password"
                        disabled={isSubmitting}
                      />
                    )}
                  </Field>
                  
                  <Field name="re_new_password">
                    {({ field }) => (
                      <Input
                        {...field}
                        type="password"
                        label="Confirm new password"
                        placeholder="Confirm your new password"
                        error={reNewPasswordError}
                        data-testid="input-confirm-password"
                        disabled={isSubmitting}
                      />
                    )}
                  </Field>

                  <Button
                    type="submit"
                    variant="primary"
                    className="w-full mb-4"
                    disabled={isSubmitting || !uid || !token}
                    data-testid="button-submit-reset-password"
                  >
                    {isSubmitting ? 'Resetting...' : 'Reset password'}
                  </Button>
                </Form>
              );
            }}
          </Formik>

          <div className="text-center">
            <button
              onClick={() => setLocation('/forgot-password')}
              className="text-sm text-[#4FC3F7] hover:text-[#3BA7D1] transition-colors"
              data-testid="link-request-new-reset"
            >
              Request a new reset link
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

