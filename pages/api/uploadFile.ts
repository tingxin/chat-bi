import type { NextApiRequest, NextApiResponse } from 'next';

import formidable from 'formidable';
import fs from 'fs';
import path from 'path';
import { Readable } from 'stream';

export const config = {
  api: {
    bodyParser: false,
  },
};

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse,
) {
  if (req.method === 'POST') {
    const form = new formidable.IncomingForm({
      maxFileSize: 5 * 1024 * 1024, // 5MB
    });

    form.parse(req, async (err, fields, files) => {
      if (err) {
        console.error('解析文件错误:', err);
        return res.status(500).json({ error: '文件上传失败' });
      }

      const file = files.file as unknown as formidable.File;
      if (!file) {
        return res.status(400).json({ error: '没有文件被上传' });
      }

      try {
        // 读取文件内容到内存
        const fileContent = await readFileContent(file);

        // Todo：在这里处理文件内容

        // 例如：解析 Excel 或 CSV 文件

        console.log('文件内容:', fileContent.slice(0, 100) + '...'); // 仅打印前100个字符

        // 返回成功响应
        res.status(200).json({
          message: '文件上传并处理成功',
          filename: file.originalFilename,
          size: file.size,
        });
      } catch (error) {
        console.error('处理文件错误:', error);
        res.status(500).json({ error: '文件处理失败' });
      }
    });
  } else {
    res.setHeader('Allow', ['POST']);
    res.status(405).end(`Method ${req.method} Not Allowed`);
  }
}

// 辅助函数：读取文件内容
function readFileContent(file: formidable.File): Promise<string> {
  return new Promise((resolve, reject) => {
    const chunks: any[] = [];
    const stream = Readable.from(file.filepath);

    stream.on('data', (chunk) => chunks.push(Buffer.from(chunk)));
    stream.on('error', (err) => reject(err));
    stream.on('end', () => resolve(Buffer.concat(chunks).toString('utf-8')));
  });
}
