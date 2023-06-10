import { Input, Select, Textarea } from "@chakra-ui/react";
import useGlobalFormik from "common/hooks/useGlobalFormik";
import { Field } from "formik";

type AppProps = {
  property: string;
};

const COMPONENT_TYPE: any = {
  select: Select,
  input: Input,
  textarea: Textarea,
};

/**
 * FormikField
 *
 * React component that setups a form input with Formik validation
 */
const FormikTextField = ({ property }: AppProps) => {
  const { formikSlice } = useGlobalFormik();

  const field = formikSlice.fieldsInfo.filter(
    (item: any) => item.property === property
  )[0];

  // * Generate ChakraUI form component: input, select, textarea
  return (
    <Field
      as={COMPONENT_TYPE[field.component]}
      placeholder={field?.placeholder}
      id={property}
      autoComplete={field.suggest}
      name={property}
      type={field.type}
      noValidate={false}
    >
      {field.options &&
        field.options.map((item: any, i: number) => (
          <option key={i}>{item}</option>
        ))}
    </Field>
  );
};

export default FormikTextField;
