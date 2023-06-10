import {
  Button,
  Divider,
  Heading,
  HStack,
  IconButton,
  Menu,
  MenuButton,
  MenuItem,
  MenuList,
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
  Text,
  VStack,
} from "@chakra-ui/react";
import useGlobalAlert from "../../../../../common/hooks/useGlobalAlert";
import useGlobalConfirm from "../../../../../common/hooks/useGlobalConfirm";
import useAPIDataAlert from "../../../../../common/hooks/useAPIDataAlert";
import useCurrentUser from "../../../../../common/hooks/useCurrentUser";
import { AdminRoleDictionary } from "../../../templates/templates";
import { UserStateType } from "../../../../../store/models";
import useAxiosWrapper from "common/hooks/useAxiosWrapper";
import { FiAlertCircle, FiAward, FiMenu, FiTrash } from "react-icons/fi";

interface AppProps {
  onClose: () => void;
  isOpen: boolean;
  selectedUser: any;
  setSelectedUser: React.Dispatch<
    React.SetStateAction<UserStateType | undefined>
  >;
  onOpen: () => void;
}

const EditUserModal = ({
  onClose,
  isOpen,
  selectedUser,
  setSelectedUser,
}: AppProps) => {
  const { user } = useCurrentUser();
  const { showGlobalAlert } = useGlobalAlert();
  const { onGlobalConfirmOpen, showGlobalConfirm } = useGlobalConfirm();
  const { postAxios: postManage } = useAxiosWrapper({
    url: "build_form/manager_user_form",
    method: "POST",
  });
  const { apiDataAlerter, standardAlertError } = useAPIDataAlert();

  // TODO: error check this, maybe one function for all of these?
  const handlePromoteDemote = async () => {
    // * Handle promote / demote
    const promoteSuccess = () => {
      setSelectedUser((prevState) => {
        if (prevState) return { ...prevState, admin: 1 };
      });
    };
    const demoteSuccess = () => {
      setSelectedUser((prevState) => {
        if (prevState) return { ...prevState, admin: 0 };
      });
    };

    try {
      // * If user has no role, promote to manager
      if (selectedUser?.admin === null || selectedUser?.admin === 0) {
        const { data } = await postManage({
          target_user: selectedUser?.email,
          action: "promoted",
        });
        apiDataAlerter({
          data: data,
          onSuccess: promoteSuccess,
          successMsg: `You have promoted ${selectedUser?.name}`,
        });
        // * If user has manager role, demote to user
      } else if (selectedUser?.admin === 1) {
        const { data } = await postManage({
          target_user: selectedUser?.email,
          action: "demoted",
        });
        apiDataAlerter({
          data: data,
          onSuccess: demoteSuccess,
          successMsg: `You have demoted ${selectedUser?.name}`,
        });
      } else {
        // * If user is admin, stop the promotion/demotion action
        showGlobalAlert(
          "Something went wrong!",
          "You cannot change an admin's role"
        );
      }
    } catch {
      standardAlertError();
    }
  };

  const handleBanUnban = async () => {
    // * Handle ban and unban
    const banSuccess = () => {
      setSelectedUser((prevState) => {
        if (prevState) return { ...prevState, active: false };
      });
    };
    const unbanSuccess = () => {
      setSelectedUser((prevState) => {
        if (prevState) return { ...prevState, active: true };
      });
    };

    // * If user is active, ban them
    try {
      // * If user is not banned, ban them
      if (selectedUser?.active) {
        const { data } = await postManage({
          target_user: selectedUser?.email,
          action: "banned",
        });
        apiDataAlerter({
          data: data,
          onSuccess: banSuccess,
          successMsg: `You have banned ${selectedUser.name}`,
        });
        // * If user is banned, unban them
      } else {
        const { data } = await postManage({
          target_user: selectedUser?.email,
          action: "un-banned",
        });
        apiDataAlerter({
          data: data,
          onSuccess: unbanSuccess,
          successMsg: `You have unbanned ${selectedUser?.name}`,
        });
      }
    } catch {
      standardAlertError();
    }
  };

  const handleDeleteUser = () => {
    const deleteSuccess = () => {
      setSelectedUser(undefined);
      onClose();
    };

    const deleteUser = async () => {
      try {
        const { data } = await postManage({
          target_user: selectedUser?.email,
          action: "deleted",
        });
        apiDataAlerter({
          data: data,
          onSuccess: deleteSuccess,
          successMsg: `You have deleted ${selectedUser?.name}`,
        });
      } catch {
        standardAlertError();
      }
    };

    if (onGlobalConfirmOpen) {
      showGlobalConfirm({
        title: "This action cannot be undone",
        desc: `Are you sure you want to delete ${selectedUser?.name}? `,
        confirm: deleteUser,
      });
      onGlobalConfirmOpen();
    }
  };

  const handleEmail = async () => {
    const successUnVerify = () => {
      setSelectedUser((prevState) => {
        if (prevState) return { ...prevState, verified: false };
      });
    };
    const successVerify = () => {
      setSelectedUser((prevState) => {
        if (prevState) return { ...prevState, verified: true };
      });
    };

    try {
      if (selectedUser?.verified) {
        const { data } = await postManage({
          target_user: selectedUser?.email,
          action: "manual un-verification",
        });
        apiDataAlerter({
          data: data,
          onSuccess: successUnVerify,
          successMsg: `You unverfied ${selectedUser.name}'s email`,
        });
        // * If user has verified email, unverify
      } else {
        const { data } = await postManage({
          target_user: selectedUser?.email,
          action: "manual verification",
        });
        apiDataAlerter({
          data: data,
          onSuccess: successVerify,
          successMsg: `You verfied ${selectedUser?.name}'s email`,
        });
      }
    } catch {
      standardAlertError();
    }
  };

  interface selectedUserPropertiesType {
    name: string;
    property: keyof UserStateType;
    editTitle?: string;
    editFunction?: () => void;
    dictionary?: any;
  }

  const selectedUserProperties: selectedUserPropertiesType[] = [
    {
      name: selectedUser?.verified ? "Verfied email" : "Unverified email",
      property: "email",
      editTitle: selectedUser?.verified ? "Unverify email" : "Verify email",
      editFunction: handleEmail,
    },

    {
      name: "Role",
      property: "admin",
      dictionary: AdminRoleDictionary,
    },
    {
      name: selectedUser?.active ? "Active account" : "Banned account",
      property: "isLoggedIn",
    },
    { name: "Company", property: "company" },
    { name: "Country", property: "country" },
    { name: "Department", property: "department" },
    { name: "Purpose", property: "purpose" },
  ];

  return (
    <Modal onClose={onClose} isOpen={isOpen} isCentered>
      <ModalOverlay />
      <ModalContent maxW="4xl">
        <ModalHeader>
          <HStack justify="space-between" pt={10}>
            <Heading>Edit {selectedUser?.name}</Heading>
            {/* Admin controls */}
            {/* TODO map and move this to own */}
            {user?.admin === 2 && (
              <Menu>
                <MenuButton
                  as={IconButton}
                  aria-label="Options"
                  icon={<FiMenu />}
                  variant="outline"
                />
                <MenuList fontSize={"md"}>
                  <MenuItem icon={<FiTrash />} onClick={handleDeleteUser}>
                    Delete user
                  </MenuItem>
                  <MenuItem icon={<FiAlertCircle />} onClick={handleBanUnban}>
                    {selectedUser?.active ? "Ban user" : "Unban user"}
                  </MenuItem>
                  <MenuItem icon={<FiAward />} onClick={handlePromoteDemote}>
                    {selectedUser?.admin === 1
                      ? "Demote to user"
                      : "Promote to manager"}
                  </MenuItem>
                </MenuList>
              </Menu>
            )}
          </HStack>
        </ModalHeader>
        <Divider />
        <ModalCloseButton />
        <ModalBody py={5}>
          <VStack align="flex-start" spacing={5}>
            {/* User properties */}
            {selectedUser &&
              selectedUserProperties.map((item, i) => (
                <>
                  <HStack key={i}>
                    <Heading fontSize="md">{item.name}</Heading>
                    <Text>
                      {item.dictionary
                        ? item.dictionary[selectedUser[item.property]]
                        : typeof selectedUser[item.property] !== "string" ||
                          selectedUser[item.property].length > 0
                        ? selectedUser[item.property]
                        : "Not available"}
                    </Text>
                    {item.editTitle && item.editFunction && (
                      <Button size={"sm"} onClick={item.editFunction}>
                        {item.editTitle}
                      </Button>
                    )}
                  </HStack>
                  <Divider />
                </>
              ))}
          </VStack>
        </ModalBody>
        <ModalFooter>
          <Button onClick={onClose}>Close</Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};

export default EditUserModal;
