import FlaskForm from "../../../common/components/FlaskForm";
import useAPIDataAlert from "../../../common/hooks/useAPIDataAlert";
import AuthCard from "../components/AuthCard";
import AuthHeading from "../components/AuthHeading";
import AuthFooter from "../components/AuthFooter";
import RouterLink from "../../../common/components/RouterLink";
import usePageTitle from "../../../common/hooks/usePageTitle";

const KEY = "verify_email_form";

/**
 * Unlock Account Page
 */
const UnlockAccountToken = () => {
  usePageTitle("Unlock account");
  const { apiDataAlerter } = useAPIDataAlert();

  // * Handles on form submit after data is sent
  const handleSubmit = (data: any) => {
    apiDataAlerter({
      data: data,
      successMsg: `You have unlocked your account ${data.success}`,
    });
  };

  return (
    <FlaskForm formKey={KEY} runAfterSubmit={handleSubmit}>
      {({ isSubmitting }) => (
        <AuthCard>
          <AuthHeading
            title="Success!"
            desc={`You have unlocked your account.`}
          />
          <AuthFooter>
            <RouterLink link="/signin" text="Back to sign in" />
          </AuthFooter>
        </AuthCard>
      )}
    </FlaskForm>
  );
};

export default UnlockAccountToken;
