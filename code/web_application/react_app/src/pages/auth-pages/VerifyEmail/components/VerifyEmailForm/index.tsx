import { Box, Button, VStack } from "@chakra-ui/react";
import FlaskField from "common/components/FlaskField";
import FlaskForm from "../../../../../common/components/FlaskForm";
import useAPIDataAlert from "../../../../../common/hooks/useAPIDataAlert";
import AuthHeading from "../../../components/AuthHeading";

const KEY = "request_email_verification_form";

interface AppProps {
  setToggle: React.Dispatch<React.SetStateAction<boolean>>;
  setEmail: React.Dispatch<React.SetStateAction<string>>;
}

/**
 * React component to request email verification
 */
const VerifyEmailForm = ({ setToggle, setEmail }: AppProps) => {
  const { apiDataAlerter } = useAPIDataAlert();

  // * Handles on form submit after data is sent
  const handleSubmit = (data: any) => {
    const resetSuccess = () => {
      setToggle(true);
      setEmail(data.success);
    };
    apiDataAlerter({
      onSuccess: resetSuccess,
      successMsg: `Email verification sent to ${data.success}`,
      data: data,
    });
  };

  return (
    <FlaskForm formKey={KEY} runAfterSubmit={handleSubmit}>
      {({ isSubmitting }) => (
        <>
          <AuthHeading
            title="Verify your email"
            desc="You will recieve instructions for verifying your email."
          />

          <VStack spacing={5}>
            {/* Email, CAPTCHA */}
            <FlaskField property="email" />
            <Box w="100%">
              <FlaskField property="math" />
            </Box>

            <Button
              type="submit"
              colorScheme="blue"
              width="full"
              isDisabled={isSubmitting}
            >
              Request email verification link
            </Button>
          </VStack>
        </>
      )}
    </FlaskForm>
  );
};

export default VerifyEmailForm;
