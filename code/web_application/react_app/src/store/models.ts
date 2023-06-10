/**
 * FormikSliceType
 *
 * Type for global formik state that keeps track of the form key, loading state, and the field info to generate the `FlaskForm` component
 */
export interface FormikSliceType {
  key: string;
  loading: boolean;
  fieldsInfo: any[];
}

/**
 * AlertType
 *
 * Type for alerts including `enabled` to keep track of when to hide the global alert
 */
export type AlertType = {
  enabled: boolean;
} & ShowAlertType;

/**
 * ShowAlertType
 *
 * Type for useGlobalAlert hook to enable a toast alert
 */
export interface ShowAlertType {
  title: string;
  desc: string;
  status?: "error" | "info" | "warning" | "success" | "loading" | undefined;
}

/**
 * ShowConfirmType
 *
 * Type for showing the confirm modal
 */
export interface ShowConfirmType {
  title: string;
  desc: string;
  confirm?: () => void;
  unconfirm?: () => void;
}

/**
 * ConfirmType
 *
 * Type for confirm modal callback functions
 */
export type ConfirmType = {
  onOpen: () => void;
  onClose: () => void;
} & ShowConfirmType;

/**
 * UserStateType
 *
 * Type for the user's information
 */
export interface UserStateType {
  csrf_token: string;
  admin: number;
  company: string;
  country: string;
  department: string;
  email: string;
  name: string;
  purpose: string;
  verified: boolean;
  isLoggedIn: boolean;
  position: string;
  id: number;
  active: boolean | null;
}
