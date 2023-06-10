import { Button, VStack } from "@chakra-ui/react";
import FlaskField from "common/components/FlaskField";
import FlaskForm from "common/components/FlaskForm";
import useAPIDataAlert from "common/hooks/useAPIDataAlert";
import { useNavigate } from "react-router-dom";
import ChangeSettingsCard from "../components/ChangeSettingsCard";

const KEY = "profile_edit_password_form";

const SettingsPassword = () => {
  const navigate = useNavigate();
  const { apiDataAlerter } = useAPIDataAlert();

  // * Handles on form submit
  const handleSubmit = (data: any, _values: any) => {
    console.log("submitted");
    // * Otherwise, alert success or give errors
    apiDataAlerter({
      data: data,
      onSuccess: () => {
        navigate("/settings");
      },
    });
  };

  return (
    <FlaskForm
      formKey={KEY}
      runAfterSubmit={handleSubmit}
      resetAfterSubmit={{
        old_password: "",
        new_password: "",
        confirm_password: "",
      }}
    >
      {({ isSubmitting }) => (
        <ChangeSettingsCard
          title="Change password"
          desc="Change your current password"
        >
          <VStack spacing={5} align="center" w="100%">
            <FlaskField property="old" />
            <FlaskField property="password" />
            <FlaskField property="confirm" />
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

export default SettingsPassword;
