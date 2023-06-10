import { Container, useDisclosure } from "@chakra-ui/react";
import { useState } from "react";

import TermsOfService from "./components/TermsOfService";
import SignUpSuccess from "./components/SignUpSuccess";
import usePageTitle from "../../../common/hooks/usePageTitle";
import SignUpForm from "./components/SignUpForm";

/**
 * SignUp
 *
 * React component that renders sign up page from backend
 */
const SignUp = () => {
  // * Changes document title to "Sign up"
  usePageTitle("Sign up");
  // * ChakraUI's modal opening commands
  const { isOpen, onOpen, onClose } = useDisclosure();
  // * Once a user successfully signs in, will send a greeting message given this state value
  const [email, setEmail] = useState("");
  const [instructions, setInstructions] = useState("")

  return (
    <>
      <TermsOfService onClose={onClose} isOpen={isOpen} />
      {email?.length === 0 ? (
        <SignUpForm setEmail={setEmail} setInstructions={setInstructions} onOpen={onOpen} />
      ) : (
        <SignUpSuccess email={email} instructions={instructions} />
      )}
    </>
  );
};
export default SignUp;
