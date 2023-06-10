import {
  Checkbox,
  FormErrorMessage,
  FormLabel,
  HStack,
} from "@chakra-ui/react";
import { Field, useFormikContext } from "formik";
import { FormControl } from "formik-chakra-ui";

import ActionLink from "../../../ActionLink";

interface AppProps {
  /**
   * `function` - Executes when clicking on the action link
   */
  action: any;
  /**
   * `string` - Form key to generate form from backend
   */
  formKey: string;
}

/**
 * FormikCheckbox
 *
 * React component that wraps ChakraUI checkbox component with formik logic for an agree to terms field
 */
const FormikTerms = ({ action, formKey }: AppProps) => {
  const formik = useFormikContext<any>();
  const { errors, touched } = formik;

  return (
    <FormControl
      as={"span"}
      isRequired
      isInvalid={!!errors["terms"] && !!touched["terms"]}
      name={"terms"}
    >
      <HStack align="center" justify="center">
        <FormLabel mb={0} htmlFor="terms">
          Agree to{" "}
          <ActionLink
            text="terms of service"
            onClick={() => {
              if (action) {
                action();
              }
            }}
          />
        </FormLabel>
        <Field as={Checkbox} name="terms" />
      </HStack>
      <FormErrorMessage>{errors["terms"]?.toString()}</FormErrorMessage>
    </FormControl>
  );
};

export default FormikTerms;
