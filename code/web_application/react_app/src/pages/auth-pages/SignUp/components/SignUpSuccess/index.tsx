import { Button, Container, Flex } from "@chakra-ui/react";
import { Link } from "react-router-dom";
import RouterLink from "../../../../../common/components/RouterLink";
import AuthFooter from "../../../components/AuthFooter";
import AuthHeading from "../../../components/AuthHeading";

interface AppProps {
  /**
   * `email` - State of email of user who successfully signs up
   * `instructions` - Instructions to be displayed for users after signup
   */
  email: string;
  instructions: string;
}

/**
 * SignUpSuccess
 *
 * React component that renders the success screen that prompts the user to verify their email
 */
const SignUpSuccess = ({ email, instructions }: AppProps) => {
  return (
    <Flex w="100vw" h="90vh" justify="center" align="center">
      <Container maxW="lg">
        <AuthHeading
          title="Account created!"
          desc={instructions}
        />
        <AuthFooter>
          <Link to="/send-verification-email">
            <Button>Resend verification email</Button>
          </Link>
          <RouterLink link="/signin" text="Back to sign in" />
        </AuthFooter>
      </Container>
    </Flex>
  );
};

export default SignUpSuccess;
