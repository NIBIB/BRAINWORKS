import { Button } from "@chakra-ui/react";
import React from "react";
import { useNavigate } from "react-router-dom";
import { brandColorScheme } from "../../../setup/theme/colors";
import useCurrentUser from "../../hooks/useCurrentUser";

/**
 * SignupLogoutButton
 *
 * React component that toggles between sign up / log out depending on if the user is logged in or not
 */
const SignupLogoutButton = () => {
  const { user } = useCurrentUser();
  const navigate = useNavigate();
  return (
    <>
      {!user.isLoggedIn && (
        <Button
          size="sm"
          colorScheme={brandColorScheme}
          onClick={() => {
            navigate("/signup");
          }}
        >
          Sign up
        </Button>
      )}
    </>
  );
};

export default SignupLogoutButton;
