import { NextApiRequest, NextApiResponse } from 'next';

import {
  BACK_USER_CLIENT_ID,
  BACK_USER_POOL_ID,
  DEFAULT_REGION,
} from '@/utils/app/const';

const handler = async (req: NextApiRequest, res: NextApiResponse) => {
  try {
    res.status(200).json({
      userPoolId: BACK_USER_POOL_ID,
      userPoolClientId: BACK_USER_CLIENT_ID,
      region: DEFAULT_REGION,
    });
  } catch (error) {
    console.error(error);
    res.status(500).json({ status: 500 });
  }
};

export default handler;
