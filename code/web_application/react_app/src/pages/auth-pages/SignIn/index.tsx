import { Button, useToast, VStack } from "@chakra-ui/react";
import RouterLink from "common/components/RouterLink";
import AuthFooter from "pages/auth-pages/components/AuthFooter";
import AuthHeading from "pages/auth-pages/components/AuthHeading";
import { useNavigate } from "react-router-dom";
import useCurrentUser from "common/hooks/useCurrentUser";
import useAPIDataAlert from "common/hooks/useAPIDataAlert";
import { UserStateType } from "store/models";
import FlaskForm from "common/components/FlaskForm";
import AuthCard from "../components/AuthCard";
import FlaskField from "common/components/FlaskField";

const KEY = "sign_in_form";

/**
 * SignIn
 *
 * React component for the sign in form with parameters generated from the back end
 */
const SignIn = () => {
  const navigate = useNavigate();
  const { setCurrentUser } = useCurrentUser();
  const { apiDataAlerter } = useAPIDataAlert();

  const toast = useToast();

  // * Handles on form submit
  const handleSubmit = (data: any, values: any) => {
    // * Successful login, sets current user state and navigates to index page
    const loginSuccess = (user: UserStateType) => {
      setCurrentUser(user);
      navigate("/");
    };
    // * Non verified user, gets a verify email toast
    if (data?.error === "You must verify your email before logging in.") {
      toast({
        title: `Please verify your email ${values.email} `,
        description: `Check your inbox for the email verification or send yourself another verification.`,
        status: "warning",
        duration: null,
        isClosable: true,
        position: "top",
      });
      navigate("/send-verification-email");
      return;
    }
    // * Otherwise, alert success or give errors
    apiDataAlerter({
      data: data,
      onSuccess: () => {
        loginSuccess(data?.success);
      },
      successMsg: `Welcome, ${data.success?.name}`,
    });
  };

  return (
    <FlaskForm
      formKey={KEY}
      runAfterSubmit={handleSubmit}
      resetAfterSubmit={{ email: "", password: "" }}
    >
      {({ isSubmitting }) => (
        <AuthCard>
          <AuthHeading
            title="Sign in"
            desc="Welcome back, let's get creating."
          />
          <VStack spacing={5} align="center" w="100%">
            <FlaskField property="email" />
            <FlaskField property="password" />
            <Button
              type="submit"
              colorScheme="blue"
              width="full"
              isDisabled={isSubmitting}
            >
              Login
            </Button>
          </VStack>
          <AuthFooter>
            <RouterLink text="Forgot password?" link="/forgotpassword" />
            <RouterLink text="Don't have an account? Sign up." link="/signup" />
          </AuthFooter>
        </AuthCard>
      )}
    </FlaskForm>
  );
};

export default SignIn;
