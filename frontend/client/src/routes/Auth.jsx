import { useState, useEffect } from 'react';
import { useLocation } from 'wouter';
import { useAuth } from '../context/AuthContext';
import { Formik, Form, Field } from 'formik';
import { loginSchema, createAccountSchema } from '../utils/validators';
import Input from '../components/Input';
import Button from '../components/Button';
import Footer from '../components/Footer';

export default function Auth() {
  const [location, setLocation] = useLocation();
  const { login, isAuthenticated, user } = useAuth();
  
  const searchParams = new URLSearchParams(location.split('?')[1]);
  const initialTab = searchParams.get('tab') === 'create' ? 'create' : 'login';
  const [activeTab, setActiveTab] = useState(initialTab);

  useEffect(() => {
    if (isAuthenticated) {
      setLocation('/dashboard');
    }
  }, [isAuthenticated, setLocation]);

  const handleSubmit = async (values, { setSubmitting }) => {
    try {
      login(values.email, values.password);
      setLocation('/dashboard');
    } catch (error) {
      console.error('Auth error:', error);
    } finally {
      setSubmitting(false);
    }
  };

  const getInitialValues = () => {
    if (activeTab === 'login') {
      return { email: '', password: '' };
    }
    return { email: '', password: '', confirmPassword: '' };
  };

  const username = user?.email ? user.email.split('@')[0] : null;
  let welcomeText = '';
  if (activeTab === 'create') {
    welcomeText = 'Sign up to start collaborating on research PDFs';
  } else if (username) {
    welcomeText = `${username}, Welcome back! Sign in to continue`;
  } else {
    welcomeText = 'Welcome back! Sign in to continue';
  }

  return (
    <div className="min-h-screen bg-[#121212] flex flex-col">
      <div className="flex-1 flex items-center justify-center px-4 py-12">
        <div className="w-full max-w-[500px]">
          <div className="bg-[#1E1E1E] border border-[#2A2A2A] rounded-lg p-8">
            <h1 className="text-2xl font-bold text-[#E0E0E0] mb-2">
              {activeTab === 'create' ? 'Create Account' : 'Login'}
            </h1>
            <p className="text-[#BDBDBD] text-sm mb-6">{welcomeText}</p>
            
            <Formik
              key={activeTab}
              initialValues={getInitialValues()}
              validationSchema={activeTab === 'login' ? loginSchema : createAccountSchema}
              onSubmit={handleSubmit}
            >
              {({ errors, touched, isSubmitting }) => (
                <Form>
                  <Field name="email">
                    {({ field }) => (
                      <Input
                        {...field}
                        type="email"
                        label="Email"
                        placeholder="researcher@university.edu"
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
                        placeholder="••••••••"
                        error={touched.password && errors.password}
                        data-testid="input-password"
                      />
                    )}
                  </Field>

                  {activeTab === 'login' && (
                    <div className="text-right mt-2">
                      <button
                        type="button"
                        onClick={() => {
                          // placeholder: show a simple prompt / later wire to reset flow
                          // keep UX lightweight for now
                          /* eslint-disable no-alert */
                          alert('Forgot password flow not implemented yet.');
                        }}
                        className="text-[#4FC3F7] text-sm hover:underline"
                        data-testid="button-forgot-password"
                      >
                        Forgot password?
                      </button>
                    </div>
                  )}

                  {activeTab === 'create' && (
                    <Field name="confirmPassword">
                      {({ field }) => (
                        <Input
                          {...field}
                          type="password"
                          label="Confirm Password"
                          placeholder="••••••••"
                          error={touched.confirmPassword && errors.confirmPassword}
                          data-testid="input-confirm-password"
                        />
                      )}
                    </Field>
                  )}

                  <Button
                    type="submit"
                    variant="primary"
                    className="w-full"
                    disabled={isSubmitting}
                    data-testid="button-submit-auth"
                  >
                    {activeTab === 'login' ? 'Login' : 'Sign Up'}
                  </Button>

                  <p className="text-center text-[#BDBDBD] text-sm mt-4">
                    {activeTab === 'login' ? (
                      <>
                        Don't have an account?{' '}
                        <button
                          type="button"
                          onClick={() => setActiveTab('create')}
                          className="text-[#4FC3F7] hover:underline"
                          data-testid="button-switch-to-create"
                        >
                          Create Account
                        </button>
                      </>
                    ) : (
                      <>
                        Already have an account?{' '}
                        <button
                          type="button"
                          onClick={() => setActiveTab('login')}
                          className="text-[#4FC3F7] hover:underline"
                          data-testid="button-switch-to-login"
                        >
                          Login
                        </button>
                      </>
                    )}
                  </p>
                </Form>
              )}
            </Formik>
          </div>
        </div>
      </div>
      
      <Footer />
    </div>
  );
}
