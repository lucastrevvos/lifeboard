export type User = {
  id: number;
  name: string;
  email: string;
};

export type Board = {
  id: number;
  name: string;
  role: string;
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
