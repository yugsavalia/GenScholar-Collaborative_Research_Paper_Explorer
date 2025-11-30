import { useState, useEffect } from 'react';
import { Formik, Form, Field } from 'formik';
import { useApp } from '../context/AppContext';
import { workspaceSchema } from '../utils/validators';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import SearchBar from '../components/SearchBar';
import WorkspaceList from '../components/WorkspaceList';
import Modal from '../components/Modal';
import Input from '../components/Input';
import Textarea from '../components/Textarea';
import Button from '../components/Button';
import Icon from '../components/Icon';

export default function Dashboard() {
  const { 
    workspaces, 
    createWorkspace
  } = useApp();
  const [searchQuery, setSearchQuery] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [createError, setCreateError] = useState('');

  const handleCreateWorkspace = async (values, { setSubmitting, resetForm, setFieldError }) => {
    setCreateError('');
    try {
      await createWorkspace(values.name, values.description);
      resetForm();
      setCreateError('');
      setIsModalOpen(false);
    } catch (error) {
      console.error('Error creating workspace:', error);
      const errorMessage = error.message || error.data?.error || error.data?.message || 'Failed to create workspace';
      setCreateError(errorMessage);
      if (errorMessage.includes('already exists')) {
        setFieldError('name', errorMessage);
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col" style={{ background: 'var(--bg-color)' }}>
      <Navbar />
      
      <div className="flex-1 max-w-[1400px] w-full mx-auto px-6 py-8">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold" style={{ color: 'var(--text-color)' }}>Workspaces</h1>
          <Button
            onClick={() => setIsModalOpen(true)}
            variant="primary"
            className="flex items-center gap-2"
            data-testid="button-create-workspace"
          >
            <Icon name="plus" size={20} />
            Create Workspace
          </Button>
        </div>

        <div className="mb-8">
          <SearchBar
            value={searchQuery}
            onChange={setSearchQuery}
            placeholder="Search workspaces..."
          />
        </div>

        <WorkspaceList workspaces={workspaces} searchQuery={searchQuery} />
      </div>

      <Footer />

      <Modal
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false);
          setCreateError('');
        }}
        title="Create New Workspace"
      >
        <Formik
          initialValues={{ name: '', description: '' }}
          validationSchema={workspaceSchema}
          onSubmit={handleCreateWorkspace}
        >
          {({ errors, touched, isSubmitting }) => (
            <Form>
              {createError && (
                <div className="mb-4 p-3 rounded-md" style={{ background: '#EF5350', color: '#fff' }}>
                  <p className="text-sm">{createError}</p>
                </div>
              )}
              <Field name="name">
                {({ field, form }) => (
                  <Input
                    {...field}
                    label="Workspace Name"
                    placeholder="Enter workspace name"
                    error={touched.name && errors.name}
                    data-testid="input-workspace-name"
                    maxLength={25}
                    onInput={(e) => {
                      if (e.target.value.length > 25) {
                        e.target.value = e.target.value.slice(0, 25);
                      }
                      if (e.target.value.length >= 25) {
                        form.setFieldTouched('name', true);
                        form.setFieldError('name', 'Max size is 25 characters');
                      }
                    }}
                  />
                )}
              </Field>

              <Field name="description">
                {({ field }) => (
                  <Textarea
                    {...field}
                    label="Description"
                    placeholder="Enter workspace description"
                    rows={4}
                    error={touched.description && errors.description}
                    data-testid="input-workspace-description"
                  />
                )}
              </Field>

              <div className="flex gap-2 justify-end">
                <Button
                  type="button"
                  variant="secondary"
                  onClick={() => setIsModalOpen(false)}
                  data-testid="button-cancel"
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="primary"
                  disabled={isSubmitting}
                  data-testid="button-submit-workspace"
                >
                  Create
                </Button>
              </div>
            </Form>
          )}
        </Formik>
      </Modal>
    </div>
  );
}
