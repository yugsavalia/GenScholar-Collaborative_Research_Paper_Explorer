import * as Yup from 'yup';

export const loginSchema = Yup.object({
  identifier: Yup.string()
    .required('Email or username is required'),
  password: Yup.string()
    .min(6, 'Password must be at least 6 characters')
    .max(15, 'Password must be at most 15 characters')
    .required('Password is required')
});

export const createAccountSchema = Yup.object({
  username: Yup.string()
    .min(3, 'Username must be at least 3 characters')
    .max(15, 'Username must be at most 15 characters')
    .matches(/^[a-zA-Z0-9_]+$/, 'Username can only contain letters, numbers, and underscores')
    .required('Username is required'),
  email: Yup.string()
    .email('Invalid email address. Please enter a valid email.')
    .required('Email is required')
    .matches(
      /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/,
      'Invalid email format. Please enter a valid email address.'
    ),
  password: Yup.string()
    .min(6, 'Password must be at least 6 characters')
    .max(15, 'Password must be at most 15 characters')
    .required('Password is required'),
  confirm_password: Yup.string()
    .required('Please confirm your password')
    .oneOf([Yup.ref('password')], 'Passwords must match')
});

export const workspaceSchema = Yup.object({
  name: Yup.string()
    .required('Workspace name is required')
    .max(25, 'Max size is 25 characters')
    .matches(
      /^[A-Za-z0-9_ ]+$/,
      'Workspace name may contain only letters, digits, underscores, and spaces.'
    )
    .matches(
      /^[A-Za-z]/,
      'Workspace name cannot start with a digit, underscore, or blank space.'
    ),
  description: Yup.string()
    .max(500, 'Description must be less than 500 characters')
});
