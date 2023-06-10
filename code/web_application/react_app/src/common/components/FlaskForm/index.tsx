import * as Yup from "yup";
import { useParams } from "react-router-dom";
import { ReactElement, useEffect, useState } from "react";
import { buildYup } from "schema-to-yup";

import useFormikState from "../../hooks/useGlobalFormik";
import FormikWrapper from "./FormikWrapper";
import useAxiosWrapper from "common/hooks/useAxiosWrapper";
// * Type for building form state
interface BuildFormType {
  key: string;
  validation_schema: any;
  initial_values: any;
  fields_info: any[];
  loading: boolean;
  hasToken: boolean;
  hasCaptcha: boolean;
  invalidToken: boolean;
  csrf_token: string;
  isSubmitting: boolean;
}

interface AppProps {
  /**
   * `string` - Form key matches with the Flask form's form key in order to generate correct form object
   */
  formKey: string;

  /**
   * `object` - Field values in this object will reset to the inital state on form submit
   */
  resetAfterSubmit?: any;
  /**
   * `function` - This callback function will run after the form is successfully submitted, good for changing the state or navigating to another page after submission
   */
  runAfterSubmit?: (data: any, values: any) => void;
  /**
   * `boolean` - Determines if form should have vanilla valiation (incorrect input popups)
   */
  noValidate?: boolean;
  /**
   * `boolean` - Save form in session for user to come back to
   */
  formSession?: boolean;
  /**
   * Render props to return isSubmitting
   */
  children: (ctx: { isSubmitting: boolean }) => ReactElement;
}

/**
 * Flask Form
 *
 * React component that wraps a `Formik Form` and returns render props with generated Formik information. Takes in the associated `form key` into draws all form information from Flask backend to ensure the same validation.
 *
 * If form is a token form (email verification, reset password, etc), it will verify the key in the URL, then either display the needed page or an invalid token page.
 *
 * If the form is a token form with one field valid (only verifying token), the form will automatically submit the form on the component load
 *
 */
const FlaskForm = ({
  formKey,
  resetAfterSubmit,
  runAfterSubmit,
  noValidate,
  formSession,
  children,
}: AppProps) => {
  // * Get request to build form on component render
  const [form, setForm] = useState<BuildFormType>({
    key: "",
    fields_info: [],
    initial_values: {},
    validation_schema: {},
    loading: true,
    hasToken: true,
    invalidToken: false,
    hasCaptcha: false,
    csrf_token: "",
    isSubmitting: false,
  });

  // * Builds form from particular form object given key
  const { getAxios: getBuildForm } = useAxiosWrapper({
    url: `build_form/${formKey}`,
    method: "GET",
  });

  // * Create post request to give form input
  const { postAxios: postFormInput } = useAxiosWrapper({
    url: `build_form/${formKey}`,
    method: "POST",
  });

  const params = useParams();
  const { setFormik, setCaptcha, resetGlobalFormik } = useFormikState();

  // * On component render, build formik form from backend parameters & validate token if given
  useEffect(() => {
    let timer: any;

    const buildForm = async () => {
      // * Reset Formik State
      resetGlobalFormik();
      setForm((prevState) => {
        return {
          ...prevState,
          key: "",
          loading: true,
        };
      });
      const { data } = await getBuildForm();
      //console.log(data);
      // * Check for token, if token field exists then post token to check for it
      // ? TODO add route matching for token fields only
      if (
        data.fields_info.filter((field: any) => field.property === "token")
          .length > 0
      ) {
        const { data: tokenData } = await postFormInput({
          validate_token: params.token,
        });
        if (tokenData.hasOwnProperty("error")) {
          setForm((prevState) => {
            return { ...prevState, invalidToken: true };
          });
        } else {
          // * If only 1 field, token field just auto submit the form to backend
          if (data.fields_info.length === 1) {
            // console.log("Only token field, just auto verify");
            const { data } = await postFormInput({
              token: params.token,
            });
            if (runAfterSubmit) {
              runAfterSubmit(data, {});
            }
          }
        }
        setForm((prevState) => {
          return { ...prevState, hasToken: true };
        });
      }

      // * Set CSRF token state, so future post requests will have token
      setForm((prevState) => {
        return {
          ...prevState,
          csrf_token: data.csrf_token,
        };
      });

      // * Create Yup schema & set to inital validation schema state
      const formSchema = buildYup(data.validation_schema, data.config);
      setForm((prevState) => {
        return {
          ...prevState,
          validation_schema: formSchema,
        };
      });

      // * Build yup has some errors
      data.fields_info
        .filter((field: any) => field.property !== "token")
        .forEach((field: any) => {
          // * If ref value exists, edit to overwrite error msg
          if (field.refValueFor.length > 0) {
            const addMatch = Yup.object().shape({
              confirm: Yup.string()
                .oneOf(
                  [Yup.ref(field.refValueFor), null],
                  `Must match with ${field.refValueFor} field`
                )
                .required("Required"),
            });
            const removed = formSchema.omit(["confirm"]);
            const add = removed.concat(addMatch);
            setForm((prevState) => {
              return {
                ...prevState,
                validation_schema: add,
              };
            });
          }
          // * If array is required, let minimum length
          if (field.required && field.component === "stringArray") {
            let newShape: any = {};
            newShape[field.property] = Yup.array()
              .of(Yup.string())
              .min(1, `${field.title} must have atleast 1 item`)
              .required();
            const addMatch = Yup.object().shape(newShape);
            const removed = formSchema.omit([field.property]);
            const add = removed.concat(addMatch);
            setForm((prevState) => {
              return {
                ...prevState,
                validation_schema: add,
              };
            });
          }
        });

      // * Set CAPTCHA state, check if CAPTCHA exists first
      const captcha = data.fields_info.filter(
        (field: any) => field.property === "math"
      );
      if (captcha.length > 0) {
        const field = captcha[0];
        setCaptcha(field.img, field.audio);
      }

      setForm((prevState) => {
        return {
          ...prevState,
          initial_values: data.initial_values,
          fields_info: data.fields_info,
          loading: false,
          csrf_token: data.csrf_token,
        };
      });
      setFormik({
        key: formKey,
        loading: false,
        fieldsInfo: data.fields_info,
      });
    };
    buildForm();
    return () => {
      // * Clear timer on component demount
      if (timer) {
        clearTimeout(timer);
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const submitTest = async (values: any, { resetForm }: any) => {
    setForm((prevState) => {
      return {
        ...prevState,
        isSubmitting: true,
      };
    });

    // * Reset certain form values if needed
    if (resetAfterSubmit) {
      resetForm({ values: { ...values, ...resetAfterSubmit } });
    }
    // * If token exists, send token along with usual form
    let sentData = { ...values };
    if (form.hasToken) {
      sentData = { ...values, token: params.token };
    }
    const { data } = await postFormInput({
      ...sentData,
    });

    if (runAfterSubmit) {
      runAfterSubmit(data, values);
    }
    setForm((prevState) => {
      return {
        ...prevState,
        isSubmitting: false,
      };
    });
  };

  // * Loads either an invalid token page or the generated form
  return (
    <>
      {!form.loading && (
        <FormikWrapper
          postFormInput={postFormInput}
          formSession={formSession}
          initialValue={form.initial_values}
          validationSchema={form.validation_schema}
          noValidate={noValidate}
          submitHandler={submitTest}
          children={children}
          isSubmitting={form.isSubmitting}
          invalidToken={form.invalidToken}
        />
      )}
    </>
  );
};

export default FlaskForm;
