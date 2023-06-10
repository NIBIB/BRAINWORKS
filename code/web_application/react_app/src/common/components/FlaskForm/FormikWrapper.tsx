import { FormikProvider, useFormik } from "formik";
import { ReactElement, useEffect } from "react";
import GeneratedForm from "./GeneratedForm";
import InvalidToken from "./InvalidToken";
import { AnimatePresence, motion } from "framer-motion";
interface AppProps {
  postFormInput: any;
  initialValue: any;
  validationSchema: any;
  noValidate: any;
  submitHandler: any;
  invalidToken: boolean;
  formSession?: boolean;
  isSubmitting: boolean;
  children: (ctx: { isSubmitting: boolean }) => ReactElement;
}

const FormikWrapper = ({
  formSession,
  postFormInput,
  initialValue,
  validationSchema,
  noValidate,
  submitHandler,
  children,
  invalidToken,
  isSubmitting,
}: AppProps) => {
  // * Formik object given parameters from backend
  const formik = useFormik({
    initialValues: initialValue,
    enableReinitialize: true,
    validationSchema: validationSchema,
    onSubmit: submitHandler,
  });

  // * Saves form in session every time value is updated
  useEffect(() => {
    let timer: ReturnType<typeof setTimeout>;
    if (formSession && formik.values) {
      timer = setTimeout(async () => {
        await postFormInput({
          save_session: true,
          values: formik.values,
        });
      }, 500);
    }
    return () => {
      if (timer) {
        clearTimeout(timer);
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [formSession, formik.values]);

  return (
    <AnimatePresence>
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
        <FormikProvider value={formik}>
          {invalidToken ? (
            // * Invalid token page
            <InvalidToken />
          ) : (
            // * Generated form
            <GeneratedForm
              handleSubmit={formik.handleSubmit}
              noValidate={noValidate}
            >
              {children({ isSubmitting })}
            </GeneratedForm>
          )}
        </FormikProvider>
      </motion.div>
    </AnimatePresence>
  );
};

export default FormikWrapper;
