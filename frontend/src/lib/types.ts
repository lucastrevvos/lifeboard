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

export type ResponseState = "yes" | "no" | "pending";

export type WeeklyDayState = {
  date: string;
  state: ResponseState;
};

export type WeeklyCategory = {
  id: number;
  name: string;
  kind: CategoryKind;
  position: number;
  days: WeeklyDayState[];
};

export type WeeklyBoard = {
  board_id: number;
  week_start: string;
  week_end: string;
  categories: WeeklyCategory[];
};

export type SavedResponse = {
  category_id: number;
  response_date: string;
  subject_user_id: number | null;
  state: ResponseState;
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
