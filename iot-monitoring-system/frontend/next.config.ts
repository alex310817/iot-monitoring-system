// next.config.ts
import path from 'path';

export default {
  sassOptions: {
    includePaths: [path.join(__dirname, 'src/styles')],
  },
};
