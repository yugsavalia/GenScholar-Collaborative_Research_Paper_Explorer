import { useState } from 'react';
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
  const { workspaces, createWorkspace } = useApp();
  const [searchQuery, setSearchQuery] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);

  const handleCreateWorkspace = (values, { setSubmitting, resetForm }) => {
    createWorkspace(values.name, values.description);
    setSubmitting(false);
    resetForm();
    setIsModalOpen(false);
  };

  return (
    <div className="min-h-screen bg-[#121212] flex flex-col">
      <Navbar />
      
      <div className="flex-1 max-w-[1400px] w-full mx-auto px-6 py-8">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-[#E0E0E0]">Workspaces</h1>
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

        <div className="mt-12 pt-8 border-t border-[#2A2A2A]">
          <h2 className="text-xl font-semibold text-[#E0E0E0] mb-4">
            Recent Collaborations
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div className="bg-[#1E1E1E] border border-[#2A2A2A] rounded-lg p-4">
              <p className="text-[#BDBDBD] text-sm">
                Collaborated on <span className="text-[#4FC3F7]">ML Research</span>
              </p>
              <p className="text-xs text-[#BDBDBD] mt-1">2 days ago</p>
            </div>
          </div>
        </div>
      </div>

      <Footer />

      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Create New Workspace"
      >
        <Formik
          initialValues={{ name: '', description: '' }}
          validationSchema={workspaceSchema}
          onSubmit={handleCreateWorkspace}
        >
          {({ errors, touched, isSubmitting }) => (
            <Form>
              <Field name="name">
                {({ field }) => (
                  <Input
                    {...field}
                    label="Workspace Name"
                    placeholder="Enter workspace name"
                    error={touched.name && errors.name}
                    data-testid="input-workspace-name"
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
