import { useState } from 'react';
import { useLocation } from 'wouter';
import { Formik, Form, Field } from 'formik';
import * as Yup from 'yup';
import { requestPasswordReset } from '../api/passwordReset';
import Input from '../components/Input';
import Button from '../components/Button';

const forgotPasswordSchema = Yup.object().shape({
  email: Yup.string()
    .email('Invalid email address')
    .required('Email is required'),
});

export default function ForgotPassword() {
  const [, setLocation] = useLocation();
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (values) => {
    try {
      setError('');
      setSuccess(false);
      setIsSubmitting(true);
      
      await requestPasswordReset(values.email);
      setSuccess(true);
    } catch (err) {
      console.error('Password reset request error:', err);
      const errorMessage = err.message || err.data?.message || 'An error occurred. Please try again.';
      setError(errorMessage);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#121212] flex items-center justify-center px-4">
      <div className="w-full max-w-[400px]">
        <div className="bg-[#1E1E1E] border border-[#2A2A2A] rounded-lg p-8">
          <h1 className="text-2xl font-bold text-[#E0E0E0] mb-2 text-center">
            Forgot Password
          </h1>
          <p className="text-[#BDBDBD] text-sm mb-6 text-center">
            Enter the email associated with your GenScholar account. If it exists, we'll email you a reset link.
          </p>
          
          <Formik
            initialValues={{ email: '' }}
            validationSchema={forgotPasswordSchema}
            onSubmit={handleSubmit}
          >
            {({ errors, touched }) => (
              <Form>
                {error && (
                  <div className="mb-4 p-3 bg-red-500/10 border border-red-500/50 rounded-md">
                    <p className="text-red-400 text-sm">{error}</p>
                  </div>
                )}
                
                {success && (
                  <div className="mb-4 p-3 bg-green-500/10 border border-green-500/50 rounded-md">
                    <p className="text-green-400 text-sm">
                      If an account with that email exists, a reset link has been sent.
                    </p>
                  </div>
                )}
                
                <Field name="email">
                  {({ field }) => (
                    <Input
                      {...field}
                      type="email"
                      label="Email"
                      placeholder="Enter your email"
                      error={touched.email && errors.email}
                      data-testid="input-email"
                      disabled={isSubmitting || success}
                    />
                  )}
                </Field>

                <Button
                  type="submit"
                  variant="primary"
                  className="w-full mb-4"
                  disabled={isSubmitting || success}
                  data-testid="button-submit-forgot-password"
                >
                  {isSubmitting ? 'Sending...' : 'Send reset link'}
                </Button>
              </Form>
            )}
          </Formik>

          <div className="text-center">
            <button
              onClick={() => setLocation('/auth')}
              className="text-sm text-[#4FC3F7] hover:text-[#3BA7D1] transition-colors"
              data-testid="link-back-to-login"
            >
              Back to login
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

