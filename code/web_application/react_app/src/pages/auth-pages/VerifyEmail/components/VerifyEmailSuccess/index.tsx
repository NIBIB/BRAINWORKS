import { Button } from "@chakra-ui/react";
import React from "react";
import AuthFooter from "../../../components/AuthFooter";
import AuthHeading from "../../../components/AuthHeading";

interface AppProps {
  email: string;
  setToggle: React.Dispatch<React.SetStateAction<boolean>>;
}

const VerifyEmailSuccess = ({ email, setToggle }: AppProps) => {
  return (
    <>
      <AuthHeading
        title="Success!"
        desc={`An email has been sent to ${email}. Please follow the link inside to verify your account before signing in. If you don't receive the email within 5 minutes, check your spam folder. Otherwise, request another email by clicking below.`}
      />
      <AuthFooter>
        <Button
          onClick={() => {
            setToggle(false);
          }}
        >
          Resend another verification email
        </Button>
      </AuthFooter>
    </>
  );
};

export default VerifyEmailSuccess;
