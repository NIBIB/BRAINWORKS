import { ReactNode } from "react";

interface AppProps {
  /**
   * `function` - runs when form is submitted
   */
  handleSubmit: any;
  noValidate?: boolean;
  children: ReactNode;
}

/**
 * GeneratedForm
 *
 * React component that wraps child in a form component and attaches a callback to the submit function
 */
const GeneratedForm = ({ children, noValidate, handleSubmit }: AppProps) => {
  // * Disable default form behavior (enter = submit)
  function onKeyDown(e: React.KeyboardEvent<HTMLFormElement>) {
    if (e.code === "Enter" || e.code === "NumpadEnter") {
      e.preventDefault();
    }
  }

  return (
    <form
      onKeyDown={onKeyDown}
      onSubmit={handleSubmit}
      noValidate={noValidate !== undefined ? noValidate : false}
    >
      {children}
    </form>
  );
};

export default GeneratedForm;
