import { FormControl, FormErrorMessage, FormLabel } from "@chakra-ui/react";
import useGlobalFormik from "common/hooks/useGlobalFormik";
import { useFormikContext } from "formik";
import { ReactNode } from "react";

interface AppProps {
  property: string;
  children: ReactNode;
  hideInvalidMsg?: boolean;
}

/**
 * FormikValidationWrapper
 *
 * React component that wraps FlaskField components with a label and error message
 */
const FormikValidationWrapper = ({
  hideInvalidMsg,
  children,
  property,
}: AppProps) => {
  const formik = useFormikContext<any>();
  const { errors } = formik;
  const { formikSlice } = useGlobalFormik();
  const field = formikSlice.fieldsInfo.filter(
    (item: any) => item.property === property
  )[0];
  return (
    <>
      <FormControl
        isRequired={field?.required ? field.required : false}
        isInvalid={!!formik.errors[property] && !!formik.touched[property]}
      >
        <FormLabel htmlFor={property}>{field?.title}</FormLabel>
        {children}
        {!hideInvalidMsg && (
          <FormErrorMessage>{errors[property]?.toString()}</FormErrorMessage>
        )}
      </FormControl>
    </>
  );
};

export default FormikValidationWrapper;
