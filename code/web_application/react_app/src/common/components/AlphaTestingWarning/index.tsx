import { Alert, AlertIcon } from "@chakra-ui/react";

const AlphaTestingWarning = () => {
  return (
    <Alert status="warning">
      <AlertIcon />
      This version of BRAINWORKS is intended for internal testing. As such, email validation is disabled.
    </Alert>
  );
};

export default AlphaTestingWarning;
