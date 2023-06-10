import { Button, useToast, VStack } from "@chakra-ui/react";
import FlaskField from "common/components/FlaskField";
import FlaskForm from "common/components/FlaskForm";
import useAPIDataAlert from "common/hooks/useAPIDataAlert";
import useCurrentUser from "common/hooks/useCurrentUser";
import { useNavigate } from "react-router-dom";
import { UserStateType } from "store/models";
import ChangeSettingsCard from "../components/ChangeSettingsCard";

const KEY = "profile_edit_email_form";

const SettingsEmail = () => {
  const navigate = useNavigate();
  const { user, setCurrentUser } = useCurrentUser();
  const { apiDataAlerter } = useAPIDataAlert();
  const toast = useToast();

  // * Handles on form submit
  const handleSubmit = (data: any, _values: any) => {
    // * Successful login, sets current user state and navigates to index page
    const editEmailSuccess = (user: UserStateType) => {
      setCurrentUser(user);
      navigate("/settings");
    };
    // * Otherwise, alert success or give errors
    apiDataAlerter({
      data: data,
      onSuccess: () => {
        editEmailSuccess(data?.success);
        if (data?.verify) {  // if the user must verify this new email
          toast({
            title: `Please verify your new email ${data?.success.email} `,
            description: `Check your inbox for the email verification in order to log in again.`,
            status: "warning",
            duration: null,
            isClosable: true,
            position: "top",
          });
        } else {  // they don't have to
          toast({
            title: `Success!`,
            description: `Your email has been changed.`,
            status: "success",
            duration: 2000,
            isClosable: true,
            position: "top",
          });
        }
      },
    });
  };

  return (
    <FlaskForm
      formKey={KEY}
      runAfterSubmit={handleSubmit}
      resetAfterSubmit={{ email: "", password: "" }}
    >
      {({ isSubmitting }) => (
        <ChangeSettingsCard
          title={`Change ${user?.email}`}
          desc="A confirmation will be sent to your new email. Click on the confirmation link to verify in order to log in again."
        >
          <VStack spacing={5} align="center" w="100%">
            <FlaskField property="email" />
            <FlaskField property="password" />
            <Button
              type="submit"
              colorScheme="blue"
              width="full"
              isDisabled={isSubmitting}
            >
              Change
            </Button>
          </VStack>
        </ChangeSettingsCard>
      )}
    </FlaskForm>
  );
};

export default SettingsEmail;
