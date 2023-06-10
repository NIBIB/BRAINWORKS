import { Button, VStack } from "@chakra-ui/react";
import FlaskField from "common/components/FlaskField";
import FlaskForm from "common/components/FlaskForm";
import useAPIDataAlert from "common/hooks/useAPIDataAlert";
import useCurrentUser from "common/hooks/useCurrentUser";
import { useNavigate } from "react-router-dom";
import { UserStateType } from "store/models";
import ChangeSettingsCard from "../components/ChangeSettingsCard";

const KEY = "profile_edit_details_form";

const SettingsAccountDetails = () => {
  const navigate = useNavigate();
  const { setCurrentUser } = useCurrentUser();
  const { apiDataAlerter } = useAPIDataAlert();

  // * Handles on form submit
  const handleSubmit = (data: any, _values: any) => {
    // * Successful login, sets current user state and navigates to index page
    const editDetailsSuccess = (user: UserStateType) => {
      setCurrentUser(user);
      navigate("/settings");
    };
    // * Otherwise, alert success or give errors
    apiDataAlerter({
      data: data,
      onSuccess: () => {
        editDetailsSuccess(data?.success);
      },
      successMsg: `Successfully changed your account information`,
    });
  };

  return (
    <FlaskForm formKey={KEY} runAfterSubmit={handleSubmit}>
      {({ isSubmitting }) => (
        <ChangeSettingsCard
          title="Change account details"
          desc="Edit name, location, work, purpose"
        >
          <VStack spacing={5} align="center" w="100%">
            <FlaskField property="name" />
            <FlaskField property="company" />
            <FlaskField property="country" />
            <FlaskField property="position" />
            <FlaskField property="department" />
            <FlaskField property="purpose" />
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

export default SettingsAccountDetails;
