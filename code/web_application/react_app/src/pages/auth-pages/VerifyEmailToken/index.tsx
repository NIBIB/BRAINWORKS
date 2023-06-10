import FlaskForm from "../../../common/components/FlaskForm";
import useAPIDataAlert from "../../../common/hooks/useAPIDataAlert";
import useCurrentUser from "../../../common/hooks/useCurrentUser";
import AuthCard from "../components/AuthCard";
import AuthHeading from "../components/AuthHeading";
import AuthFooter from "../components/AuthFooter";
import RouterLink from "../../../common/components/RouterLink";
import usePageTitle from "../../../common/hooks/usePageTitle";

const KEY = "verify_email_form";

/**
 *  VerifiedEmailToken
 *
 *  React component that confirms verify email token
 */
const VerifiedEmailToken = () => {
  usePageTitle("Verify email");
  const { user } = useCurrentUser();
  const { apiDataAlerter } = useAPIDataAlert();

  // * Handles on form submit after data is sent
  const handleSubmit = (data: any) => {
    apiDataAlerter({
      data: data,
      successMsg: `You have verified your email ${data.success}`,
    });
  };

  return (
    <FlaskForm formKey={KEY} runAfterSubmit={handleSubmit}>
      {({ isSubmitting }) => (
        <AuthCard>
          <AuthHeading
            title="Success!"
            desc={`You have verified your email!`}
          />
          <AuthFooter>
            {!user.isLoggedIn ? (
              <RouterLink link="/signin" text="Back to sign in" />
            ) : (
              <RouterLink link="/" text="Get started" />
            )}
          </AuthFooter>
        </AuthCard>
      )}
    </FlaskForm>
  );
};

export default VerifiedEmailToken;
