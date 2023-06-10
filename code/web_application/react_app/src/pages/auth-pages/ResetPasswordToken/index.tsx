import usePageTitle from "../../../common/hooks/usePageTitle";

import { Button, VStack } from "@chakra-ui/react";
import { useNavigate } from "react-router-dom";
import useAPIDataAlert from "common/hooks/useAPIDataAlert";
import FlaskForm from "common/components/FlaskForm";
import AuthCard from "../components/AuthCard";
import AuthHeading from "../components/AuthHeading";
import AuthFooter from "../components/AuthFooter";
import RouterLink from "common/components/RouterLink";
import FlaskField from "common/components/FlaskField";

const KEY = "reset_password_form";

/**
 * React component for the reset password form
 */
const ResetPasswordForm = () => {
  usePageTitle("Reset password");
  const { apiDataAlerter } = useAPIDataAlert();
  const navigate = useNavigate();

  // * Handles on form submit after data is sent
  const handleSubmit = (data: any) => {
    // * Move to sign in screen
    const resetPassSuccess = () => {
      navigate("/signin");
    };
    // * Alert to user status
    apiDataAlerter({
      data: data,
      onSuccess: resetPassSuccess,
      successMsg: `You have successfully reset your password to ${data.success}`,
    });
  };

  return (
    <FlaskForm formKey={KEY} runAfterSubmit={handleSubmit}>
      {({ isSubmitting }) => (
        <AuthCard>
          <AuthHeading title="Reset password" desc={`Enter a new password`} />
          <VStack spacing={5} align="center">
            {/* New password, confirm password */}
            <FlaskField property="password" />
            <FlaskField property="confirm" />
            <Button
              type="submit"
              colorScheme="blue"
              width="full"
              isDisabled={isSubmitting}
            >
              Reset password
            </Button>
          </VStack>
          <AuthFooter>
            <RouterLink link="/signin" text="Back to sign in" />
          </AuthFooter>
        </AuthCard>
      )}
    </FlaskForm>
  );
};

export default ResetPasswordForm;
