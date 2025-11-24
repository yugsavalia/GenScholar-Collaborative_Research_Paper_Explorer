import { useState, useEffect } from 'react';
import { useLocation } from 'wouter';
import { Formik, Form, Field } from 'formik';
import { useAuth } from '../context/AuthContext';
import { loginSchema, createAccountSchema } from '../utils/validators';
import Input from '../components/Input';
import Button from '../components/Button';

export default function Auth() {
  const [location, setLocation] = useLocation();
  const { login, signup, isAuthenticated } = useAuth();
  
  const searchParams = new URLSearchParams(location.split('?')[1]);
  const initialTab = searchParams.get('tab') === 'create' ? 'create' : 'login';
  const [activeTab, setActiveTab] = useState(initialTab);
  const [error, setError] = useState('');

  useEffect(() => {
    if (isAuthenticated) {
      setLocation('/dashboard');
    }
  }, [isAuthenticated, setLocation]);

  const handleSubmit = async (values, { setSubmitting }) => {
    try {
      setError(''); // Clear previous errors
      
      if (activeTab === 'login') {
        // Login
        await login(values.email, values.password);
        setLocation('/dashboard');
      } else {
        // Signup - use password for both password1 and password2
        await signup(values.email, values.password, values.password);
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
    <div className="min-h-screen bg-[#121212] flex items-center justify-center px-4">
      <div className="w-full max-w-[400px]">
        <div className="bg-[#1E1E1E] border border-[#2A2A2A] rounded-lg p-8">
          <h1 className="text-2xl font-bold text-[#E0E0E0] mb-6 text-center">
            GenScholar
          </h1>
          
          <div className="flex mb-6 border-b border-[#2A2A2A]">
            <button
              onClick={() => {
                setActiveTab('login');
                setError(''); // Clear error when switching tabs
              }}
              className={`flex-1 pb-3 text-sm font-medium transition-colors ${
                activeTab === 'login'
                  ? 'text-[#4FC3F7] border-b-2 border-[#4FC3F7]'
                  : 'text-[#BDBDBD] hover:text-[#E0E0E0]'
              }`}
              data-testid="button-tab-login"
            >
              Login
            </button>
            <button
              onClick={() => {
                setActiveTab('create');
                setError(''); // Clear error when switching tabs
              }}
              className={`flex-1 pb-3 text-sm font-medium transition-colors ${
                activeTab === 'create'
                  ? 'text-[#4FC3F7] border-b-2 border-[#4FC3F7]'
                  : 'text-[#BDBDBD] hover:text-[#E0E0E0]'
              }`}
              data-testid="button-tab-create"
            >
              Create Account
            </button>
          </div>

          <Formik
            initialValues={{ email: '', password: '' }}
            validationSchema={activeTab === 'login' ? loginSchema : createAccountSchema}
            onSubmit={handleSubmit}
          >
            {({ errors, touched, isSubmitting }) => (
              <Form>
                {error && (
                  <div className="mb-4 p-3 bg-red-500/10 border border-red-500/50 rounded-md">
                    <p className="text-red-400 text-sm">{error}</p>
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
                    />
                  )}
                </Field>

                <Button
                  type="submit"
                  variant="primary"
                  className="w-full"
                  disabled={isSubmitting}
                  data-testid="button-submit-auth"
                >
                  {activeTab === 'login' ? 'Login' : 'Create Account'}
                </Button>
              </Form>
            )}
          </Formik>
        </div>
      </div>
    </div>
  );
}
