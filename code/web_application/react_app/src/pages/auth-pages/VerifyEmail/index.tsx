import { VStack } from "@chakra-ui/react";
import { useState } from "react";

import RouterLink from "../../../common/components/RouterLink";
import usePageTitle from "../../../common/hooks/usePageTitle";
import AuthCard from "../components/AuthCard";
import VerifyEmailForm from "./components/VerifyEmailForm";
import VerifyEmailSuccess from "./components/VerifyEmailSuccess";

/**
 * Send Verify Email Form
 */
const VerifyEmail = () => {
  usePageTitle("Verify email");
  const [email, setEmail] = useState("");
  const [toggle, setToggle] = useState(false);

  return (
    <AuthCard>
      <VStack spacing={3}>
        {toggle ? (
          <VerifyEmailSuccess email={email} setToggle={setToggle} />
        ) : (
          <VerifyEmailForm setEmail={setEmail} setToggle={setToggle} />
        )}
        <RouterLink link="/signin" text="Back to sign in" />
      </VStack>
    </AuthCard>
  );
};

export default VerifyEmail;
