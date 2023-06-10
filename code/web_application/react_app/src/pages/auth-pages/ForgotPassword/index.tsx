import { useState } from "react";

import AuthCard from "../components/AuthCard";
import usePageTitle from "../../../common/hooks/usePageTitle";

/**
 * Forgot password page
 */
import { Box, Button, VStack } from "@chakra-ui/react";
import ActionLink from "common/components/ActionLink";
import RouterLink from "common/components/RouterLink";
import AuthFooter from "pages/auth-pages/components/AuthFooter";
import AuthHeading from "pages/auth-pages/components/AuthHeading";
import useAPIDataAlert from "common/hooks/useAPIDataAlert";
import FlaskForm from "common/components/FlaskForm";
import { useNavigate } from "react-router-dom";
import FlaskField from "common/components/FlaskField";

const KEY = "forgot_password_form";

/**
 * ForgotPasswordForm
 *
 * React component for the forgot password form with parameters generated from the back end
 */
const ForgotPasswordForm = () => {
  usePageTitle("Forgot password");
  const [email, setEmail] = useState("");
  const { apiDataAlerter } = useAPIDataAlert();
  const navigate = useNavigate();

  // * Handles on form submit after data is sent
  const handleSubmit = (data: any) => {
    const resetSuccess = () => {
      setEmail(data?.success);
      navigate("/signin");
    };
    console.log(data)
    apiDataAlerter({
      data: data,
      onSuccess: resetSuccess,
      successMsg: `You have successfully sent your password reset request to ${data?.success}`,
      failureMsg: data?.error
    });
  };
  return (
    <FlaskForm
      formKey={KEY}
      runAfterSubmit={handleSubmit}
      resetAfterSubmit={{ email: "", math: "" }}
    >
      {({ isSubmitting }) => (
        <AuthCard>
          <AuthHeading
            title="Forgot password?"
            desc="You will receive an email with instructions for resetting your password."
          />
          <VStack spacing={5} align="center">
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
              Request reset link
            </Button>
          </VStack>
          <AuthFooter>
            <RouterLink text="Back to sign in" link="/signin" />
            {/* Send another password change request */}
            {email.length > 0 && (
              <ActionLink
                onClick={() => {
                  setEmail("");
                }}
                text="Send another password reset request."
              />
            )}
          </AuthFooter>
        </AuthCard>
      )}
    </FlaskForm>
  );
};

export default ForgotPasswordForm;
