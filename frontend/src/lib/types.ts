export type User = {
  id: number;
  name: string;
  email: string;
};

export type Board = {
  id: number;
  name: string;
  role: "owner" | "member";
};

export type InvitationStatus = "pending" | "accepted" | "declined";

export type Invitation = {
  id: number;
  board_id: number;
  invited_user_id: number;
  status: InvitationStatus;
};

export type PendingInvitation = {
  id: number;
  board_id: number;
  board_name: string;
  invited_by_user_id: number;
  invited_by_name: string;
  status: "pending";
  created_at: string;
};

export type CategoryKind = "individual" | "shared";

export type Category = {
  id: number;
  board_id: number;
  name: string;
  kind: CategoryKind;
  position: number;
};

export type CreateCategoryInput = {
  name: string;
  kind: CategoryKind;
  position: number;
};

export type RegisterInput = {
  name: string;
  email: string;
  password: string;
};

export type LoginInput = {
  email: string;
  password: string;
};
