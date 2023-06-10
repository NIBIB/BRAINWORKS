import {
  NumberInput,
  NumberInputField,
  NumberInputStepper,
  NumberIncrementStepper,
  NumberDecrementStepper,
} from "@chakra-ui/react";
import { useFormikContext } from "formik";

interface AppProps {
  /**
   * `string` is the name of the property
   */
  property: string;
}

const FormikNumberInput = ({ property }: AppProps) => {
  const { values, setFieldValue } = useFormikContext<any>();

  // * Returns all field info, give property

  const handleNumberInputChange = (value: string) => {
    setFieldValue(property, value);
  };

  return (
    <NumberInput
      onChange={handleNumberInputChange}
      w="100%"
      value={values[property]}
      min={1}
      bg="white"
      max={999}
    >
      <NumberInputField />
      <NumberInputStepper>
        <NumberIncrementStepper />
        <NumberDecrementStepper />
      </NumberInputStepper>
    </NumberInput>
  );
};

export default FormikNumberInput;
