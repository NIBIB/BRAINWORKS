import {
  Button,
  Card,
  CardBody,
  Container,
  Divider,
  Flex,
  SimpleGrid,
  VStack,
} from "@chakra-ui/react";
import FlaskField from "common/components/FlaskField";
import RouterLink from "common/components/RouterLink";
import AuthFooter from "pages/auth-pages/components/AuthFooter";
import AuthHeading from "pages/auth-pages/components/AuthHeading";

import FlaskForm from "../../../../../common/components/FlaskForm";
import FormikTerms from "../../../../../common/components/FlaskField/blocks/FormikTerms";
import useAPIDataAlert from "../../../../../common/hooks/useAPIDataAlert";

const KEY = "sign_up_form";

interface AppProps {
  /**
   * `function` - Callback for ChakraUI's open modal which opens the TOS screen
   */
  onOpen: () => void;
  /**
   * `function` - Setter for email when user successfully signs up, so the success screen can display their email
   */
  setEmail: React.Dispatch<React.SetStateAction<string>>;
  setInstructions: React.Dispatch<React.SetStateAction<string>>;  // sets the instructions to be displayed after signup
}

/**
 * SignUpForm
 *
 * React component that renders the sign up form from the backend
 */
const SignUpForm = ({ onOpen, setEmail, setInstructions }: AppProps) => {
  const { apiDataAlerter } = useAPIDataAlert();

  // * Handles on form submit after data is sent
  const handleSubmit = (data: any) => {
    const createSuccess = () => {
      setEmail(data?.email);
      setInstructions(data?.instructions)
    };
    apiDataAlerter({
      onSuccess: createSuccess,
      data: data,
      successMsg: data?.success,
      failureMsg: data?.error
    });

  };

  return (
    <FlaskForm
      formKey={KEY}
      runAfterSubmit={handleSubmit}
      resetAfterSubmit={{ password: "", confirm: "", math: "" }}
    >
      {({ isSubmitting }) => (
        <Flex w="100vw" minHeight="90vh" justify="center" align="center">
          <Card bg="white" maxW="2xl" p={5} my={50}>
            <CardBody>
              <AuthHeading
                title="Create an account."
                desc=" Gain full access to our tools by creating an account."
              />
              <SimpleGrid columns={{ base: 1, sm: 2 }} spacing={3} pb={3}>
                {/* Name, email, password, confirm password */}
                <FlaskField property="name" />
                <FlaskField property="email" />
                <FlaskField property="password" />
                <FlaskField property="confirm" />
              </SimpleGrid>
              <VStack spacing={3}>
                <SimpleGrid columns={{ base: 1, sm: 4 }} spacing={3} w="100%">
                  {/* Company, country, position, department */}
                  <FlaskField property="company" />
                  <FlaskField property="country" />
                  <FlaskField property="position" />
                  <FlaskField property="department" />
                </SimpleGrid>
                {/* Why BRAINWORKS */}
                <Flex
                  justify="center"
                  w="100%"
                  gap={5}
                  direction={{ base: "column", sm: "row" }}
                >
                  <VStack justify="center" align="space-between" w="50%">
                    <FlaskField property="purpose" />
                    <FormikTerms action={onOpen} formKey={KEY} />
                  </VStack>
                  <FlaskField property="math" />
                </Flex>
                <Divider />
                <Button
                  type="submit"
                  colorScheme="blue"
                  width="xs"
                  isDisabled={isSubmitting}
                >
                  Sign up
                </Button>
              </VStack>
              <AuthFooter>
                <RouterLink
                  text="Already have an account? Sign in"
                  link={"/signin"}
                />
              </AuthFooter>
            </CardBody>
          </Card>
        </Flex>
      )}
    </FlaskForm>
  );
};

export default SignUpForm;
