import { Search2Icon } from "@chakra-ui/icons";
import {
  Button,
  Center,
  Input,
  InputGroup,
  InputLeftElement,
  TableContainer,
  useDisclosure,
  VStack,
} from "@chakra-ui/react";
import useAxios from "axios-hooks";
import React, { useEffect, useState } from "react";
import { Table, Thead, Tbody, Tr, Th, Td } from "@chakra-ui/react";

import { gray300 } from "../../../../../setup/theme/colors";
import EditUserModal from "./EditUserModal";
import { API_URL } from "../../../../../common/templates/api";
import { AdminRoleDictionary } from "../../../templates/templates";
import useAxiosConfig from "../../../../../common/hooks/useAxiosConfig";
import { UserStateType } from "../../../../../store/models";
import useAxiosWrapper from "common/hooks/useAxiosWrapper";

// TODO: error check
const UserManager = () => {
  const [search, setSearch] = useState("");
  const [selectedUser, setSelectedUser] = useState<UserStateType>();
  const [userData, setUserData] = useState<UserStateType[]>([]);
  const { isOpen, onOpen, onClose } = useDisclosure();

  // * Fetching user data, by posting the search query
  const { postAxios: postQuery } = useAxiosWrapper({
    url: "build_form/search_user_form",
    method: "POST",
  });

  // * Every 0.7 seconds when a user types, call that query
  useEffect(() => {
    const timer = setTimeout(async () => {
      const { data } = await postQuery({ query: search, page: 1 });
      if (data?.success) {
        setUserData(data.success?.users);
      }
    }, 700);
    return () => {
      clearTimeout(timer);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search, isOpen]);

  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearch(e.target.value);
  };

  const handleMangerUser = (user: UserStateType) => {
    setSelectedUser(user);
    onOpen();
  };

  return (
    <>
      <EditUserModal
        isOpen={isOpen}
        onClose={onClose}
        onOpen={onOpen}
        selectedUser={selectedUser}
        setSelectedUser={setSelectedUser}
      />
      <VStack w="100%">
        <InputGroup>
          <InputLeftElement
            pointerEvents="none"
            children={<Search2Icon color={gray300} />}
          />
          <Input
            onChange={handleSearch}
            value={search}
            placeholder="Search for a user's name, email address, or ID"
            bg="white"
          />
        </InputGroup>

        <TableContainer
          h={500}
          w="100%"
          overflowY="auto"
          border="1px"
          borderColor="gray.200"
          pos="relative"
          bg="white"
        >
          <Table variant="simple">
            <Thead>
              <Tr>
                <Th isNumeric>ID</Th>
                <Th>Name</Th>
                <Th>Email</Th>
                <Th>Role</Th>
                <Th></Th>
              </Tr>
            </Thead>
            <Tbody>
              {/* Only render data if there is no errors & has valid data */}
              {userData &&
              userData.length > 0 &&
              !userData.hasOwnProperty("error") ? (
                userData?.map((item: UserStateType) => (
                  <Tr key={item.id}>
                    <Td isNumeric>{item.id}</Td>
                    <Td>{item.name}</Td>
                    <Td>{item.email}</Td>
                    <Td>{AdminRoleDictionary[item.admin]}</Td>
                    {/* Open edit user modal */}
                    <Td>
                      <Button
                        onClick={() => {
                          handleMangerUser(item);
                        }}
                      >
                        Manage
                      </Button>
                    </Td>
                  </Tr>
                ))
              ) : (
                <Center color={gray300} pos={"absolute"} w="100%" h="80%">
                  No users found
                </Center>
              )}
            </Tbody>
          </Table>
        </TableContainer>
      </VStack>
    </>
  );
};

export default UserManager;
