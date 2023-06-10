import useGlobalFormik from "common/hooks/useGlobalFormik";
import ImageCAPTCHA from "./blocks/FormikImageCaptcha";
import FormikNumberInput from "./blocks/FormikNumberInput";
import FormikStringArray from "./blocks/FormikStringArray";
import FormikTextField from "./blocks/FormikTextField";
import FormikValidationWrapper from "./blocks/FormikValidationWrapper";

interface AppProps {
  /**
   * Name of property
   */
  property: string;
}

/**
 * FlaskField
 *
 * React component that determines which field input should be rendered
 */
const FlaskField = ({ property }: AppProps) => {
  const { formikSlice } = useGlobalFormik();

  const field = formikSlice.fieldsInfo.filter(
    (item: any) => item.property === property
  )[0];

  // * Image CAPTCHA
  if (field.component === "math") {
    return <ImageCAPTCHA />;
  }

  // * String array
  if (field.component === "stringArray") {
    return (
      <FormikValidationWrapper
        property={property}
        children={<FormikStringArray property={property} />}
      ></FormikValidationWrapper>
    );
  }

  // * Number
  if (field.component === "number") {
    return (
      <FormikValidationWrapper
        property={property}
        children={<FormikNumberInput property={property} />}
      />
    );
  }

  // * Select, input or text area
  if (
    field.component === "select" ||
    field.component === "input" ||
    field.component === "textarea"
  ) {
    return (
      <FormikValidationWrapper
        property={property}
        children={<FormikTextField property={property} />}
      ></FormikValidationWrapper>
    );
  }
  return <div>Component does not have valid match</div>;
};

export default FlaskField;
